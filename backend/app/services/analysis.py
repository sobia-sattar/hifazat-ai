from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.models import Analysis, Comment, Prediction, Video
from app.genai.explain import generate_explanation, generate_video_summary
from app.ml.infer import analyze_batch, analyze_text, model_status
from app.services.stats import compute_comment_stats
from app.youtube.client import YouTubeAPIError, fetch_comments, fetch_video_metadata, resolve_url

DEMO_NOTICE = "DEMO MODE — these comments are bundled examples, not real YouTube comments. Do not use them for research claims."


def load_demo_bundle() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data_dir = get_settings().data_dir / "demo"
    video = json.loads((data_dir / "demo_video.json").read_text(encoding="utf-8"))
    comments = json.loads((data_dir / "demo_comments.json").read_text(encoding="utf-8"))
    return video, comments


def persist_analysis(
    db: Session,
    *,
    video_meta: dict[str, Any],
    comments: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    demo: bool,
    source: str,
    stats: dict[str, Any],
    genai_summary: str | None,
) -> Analysis:
    video = db.query(Video).filter(Video.video_id == video_meta["video_id"]).one_or_none()
    if video is None:
        video = Video(
            video_id=video_meta["video_id"],
            title=video_meta.get("title") or "",
            channel=video_meta.get("channel") or "",
            published_at=video_meta.get("published_at"),
            thumbnail_url=video_meta.get("thumbnail_url") or "",
            is_demo=demo,
        )
        db.add(video)
        db.flush()
    else:
        video.title = video_meta.get("title") or video.title
        video.channel = video_meta.get("channel") or video.channel
        video.thumbnail_url = video_meta.get("thumbnail_url") or video.thumbnail_url

    status = model_status()
    analysis = Analysis(
        video_id=video.id,
        source=source,
        demo_mode=demo,
        model_name=(status.get("selected_model") or "untrained"),
        status="complete",
        stats={**stats, "genai_summary": genai_summary, "demo_notice": DEMO_NOTICE if demo else None},
    )
    db.add(analysis)
    db.flush()

    for raw, pred in zip(comments, predictions):
        c = Comment(
            video_id=video.id,
            youtube_comment_id=raw.get("id"),
            original_text=raw.get("text") or "",
            normalized_text=pred.get("normalized_text") or "",
            published_at=raw.get("published_at"),
            is_demo=demo,
        )
        db.add(c)
        db.flush()
        db.add(
            Prediction(
                comment_id=c.id,
                analysis_id=analysis.id,
                model_name=analysis.model_name,
                language=pred.get("language"),
                language_confidence=pred.get("language_confidence") or 0,
                script=pred.get("script"),
                is_code_mixed=bool(pred.get("is_code_mixed")),
                classification=pred.get("classification"),
                confidence=pred.get("confidence") or 0,
                risk=pred.get("risk"),
                categories=pred.get("categories") or {},
                code_mix_tokens=pred.get("code_mix_tokens") or [],
                xai=pred.get("xai") or {},
                genai_explanation=pred.get("genai_explanation"),
            )
        )
    db.commit()
    db.refresh(analysis)
    return analysis


def analyze_youtube(db: Session, url: str, max_comments: int, include_genai_summary: bool) -> dict[str, Any]:
    settings = get_settings()
    demo = (not settings.youtube_enabled) or settings.force_demo_mode
    if demo:
        video_meta, comments = load_demo_bundle()
        source = "demo"
    else:
        try:
            vid = resolve_url(url)
            video_meta = fetch_video_metadata(vid)
            comments = fetch_comments(vid, max_comments=max_comments)
            if not comments:
                raise YouTubeAPIError("No comments were available for this video.", "no_comments")
            source = "youtube"
        except YouTubeAPIError as exc:
            return {"ok": False, "error": str(exc), "code": exc.code, "demo_available": True}

    # Compute ML scores + language detection for every comment.
    # Compute XAI + GenAI lazily for high-risk comments only (performance).
    from app.youtube.validation import supported_comments
    comments, skipped = supported_comments(comments)
    predictions = analyze_batch([c["text"] for c in comments], include_xai=False) if comments else []
    from app.services.moderation import observe
    observe(db, video_meta, comments, predictions, demo=demo)
    for i, pred in enumerate(predictions):
        if pred.get("risk") in {"HIGH", "CRITICAL"}:
            # Re-run only for XAI evidence.
            detailed = analyze_text(comments[i]["text"], include_xai=True)
            pred["xai"] = detailed.get("xai") or pred.get("xai") or {}
            pred["why"] = detailed.get("why") or pred.get("why") or ""
            pred["genai_explanation"] = generate_explanation(
                original_text=pred["original_text"],
                classification=pred["classification"],
                confidence=pred["confidence"],
                language=pred["language"],
                categories=pred["categories"],
                xai=pred.get("xai") or {},
            )
        else:
            pred["genai_explanation"] = None

    stats = compute_comment_stats(predictions)
    stats['skipped'] = skipped
    summary = None
    if include_genai_summary:
        summary = generate_video_summary(
            {
                "video": {k: video_meta.get(k) for k in ("title", "channel", "video_id")},
                "stats": {k: stats[k] for k in stats if k != "trend"},
                "demo": demo,
            }
        )
    analysis = persist_analysis(
        db,
        video_meta=video_meta,
        comments=comments,
        predictions=predictions,
        demo=demo,
        source=source,
        stats=stats,
        genai_summary=summary,
    )
    return serialize_analysis(db, analysis.id)


def prediction_to_row(pred: Prediction, comment: Comment) -> dict[str, Any]:
    cats = pred.categories or {}
    active = [k for k, v in cats.items() if k != "SAFE" and float(v or 0) >= 0.5]
    return {
        "id": pred.id,
        "comment_id": comment.id,
        "original_text": comment.original_text,
        "normalized_text": comment.normalized_text,
        "published_at": comment.published_at,
        "language": pred.language,
        "language_confidence": pred.language_confidence,
        "script": pred.script,
        "is_code_mixed": pred.is_code_mixed,
        "code_mix_tokens": pred.code_mix_tokens,
        "classification": pred.classification,
        "confidence": pred.confidence,
        "risk": pred.risk,
        "categories": cats,
        "category": active[0] if active else pred.classification,
        "xai": pred.xai,
        "genai_explanation": pred.genai_explanation,
        "is_demo": comment.is_demo,
    }


def serialize_analysis(db: Session, analysis_id: int) -> dict[str, Any]:
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).one()
    video = db.query(Video).filter(Video.id == analysis.video_id).one_or_none()
    preds = db.query(Prediction).filter(Prediction.analysis_id == analysis.id).all()
    comments = {c.id: c for c in db.query(Comment).filter(Comment.video_id == analysis.video_id).all()}
    rows = [prediction_to_row(p, comments[p.comment_id]) for p in preds if p.comment_id in comments]
    return {
        "ok": True,
        "analysis_id": analysis.id,
        "demo_mode": analysis.demo_mode,
        "demo_notice": DEMO_NOTICE if analysis.demo_mode else None,
        "source": analysis.source,
        "model_name": analysis.model_name,
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        "video": {
            "video_id": video.video_id if video else None,
            "title": video.title if video else None,
            "channel": video.channel if video else None,
            "published_at": video.published_at if video else None,
            "thumbnail_url": video.thumbnail_url if video else None,
        },
        "stats": analysis.stats or compute_comment_stats(rows),
        "comments": rows,
        "ethics": "AI predictions may contain errors. High-risk content should be reviewed by a human moderator.",
        "model_status": model_status(),
    }


def latest_analysis(db: Session) -> dict[str, Any] | None:
    a = db.query(Analysis).order_by(Analysis.id.desc()).first()
    if a is None:
        return None
    return serialize_analysis(db, a.id)
