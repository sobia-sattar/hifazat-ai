import os
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.runtime import high_threshold, low_threshold, set_thresholds
from app.database.models import Comment, Prediction, Review
from app.database.session import get_db
from app.genai.explain import UNAVAILABLE, generate_explanation
from app.ml.infer import analyze_text, load_research_metrics, model_status
from app.schemas import LiveStartRequest, ReviewRequest, SettingsUpdate, TextAnalyzeRequest, YouTubeAnalyzeRequest
from app.services.analysis import analyze_youtube, latest_analysis, serialize_analysis
from app.services.live import manager
from app.services.reports import comments_csv, comments_json, comments_pdf
from app.services.stats import compute_comment_stats

router = APIRouter()


@router.get("/health")
def health():
    s = get_settings()
    return {
        "app": s.app_name,
        "youtube": "enabled" if s.youtube_enabled else "demo",
        "genai": "enabled" if s.genai_enabled else "unavailable",
        "model": model_status(),
    }


@router.post("/analyze/text")
def analyze_text_endpoint(body: TextAnalyzeRequest):
    pred = analyze_text(body.text, include_xai=True)
    genai = UNAVAILABLE
    if body.include_genai or pred.get("risk") in {"HIGH", "CRITICAL"}:
        genai = generate_explanation(
            original_text=pred["original_text"],
            classification=pred["classification"],
            confidence=pred["confidence"],
            language=pred["language"],
            categories=pred["categories"],
            xai=pred.get("xai") or {},
            safer_rephrase=body.safer_rephrase,
        )
    pred["genai_explanation"] = genai
    pred["ethics"] = "AI predictions may contain errors. High-risk content should be reviewed by a human moderator."
    return pred


@router.post("/youtube/analyze")
def youtube_analyze(body: YouTubeAnalyzeRequest, db: Session = Depends(get_db)):
    result = analyze_youtube(db, body.url, body.max_comments, body.include_genai_summary)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail={"message": result.get("error"), "code": result.get("code")})
    return result


@router.get("/youtube/latest")
def youtube_latest(db: Session = Depends(get_db)):
    data = latest_analysis(db)
    if data is None:
        return {"ok": False, "message": "No analysis yet."}
    return data


@router.get("/youtube/{analysis_id}")
def youtube_get(analysis_id: int, db: Session = Depends(get_db)):
    try:
        return serialize_analysis(db, analysis_id)
    except Exception:
        raise HTTPException(status_code=404, detail={"message": "Analysis not found."})


@router.get("/comments/{prediction_id}")
def comment_detail(prediction_id: int, db: Session = Depends(get_db)):
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).one_or_none()
    if pred is None:
        raise HTTPException(status_code=404, detail={"message": "Comment not found."})
    comment = db.query(Comment).filter(Comment.id == pred.comment_id).one()
    from app.services.analysis import prediction_to_row

    row = prediction_to_row(pred, comment)
    row["ethics"] = "AI predictions may contain errors. High-risk content should be reviewed by a human moderator."
    xai_method = (row.get("xai") or {}).get("method")
    if not xai_method or xai_method == "unavailable":
        # Compute XAI on demand for evidence-grounded "WHY" views.
        detailed = analyze_text(comment.original_text, include_xai=True)
        row["xai"] = detailed.get("xai") or row.get("xai") or {}
        row["why"] = detailed.get("why") or row.get("why") or ""
        pred.xai = row["xai"]
        pred.confidence = detailed.get("confidence") or pred.confidence
        pred.language = detailed.get("language") or pred.language
        pred.language_confidence = detailed.get("language_confidence") or pred.language_confidence
        pred.script = detailed.get("script") or pred.script
        pred.is_code_mixed = bool(detailed.get("is_code_mixed"))
        pred.classification = detailed.get("classification") or pred.classification
        pred.risk = detailed.get("risk") or pred.risk
        pred.categories = detailed.get("categories") or pred.categories
        pred.code_mix_tokens = detailed.get("code_mix_tokens") or pred.code_mix_tokens
        db.add(pred)
        db.commit()
    if not row.get("genai_explanation"):
        row["genai_explanation"] = generate_explanation(
            original_text=row["original_text"],
            classification=row["classification"],
            confidence=row["confidence"],
            language=row["language"],
            categories=row["categories"],
            xai=row.get("xai") or {},
        )
    return row


@router.post("/comments/{prediction_id}/review")
def review_comment(prediction_id: int, body: ReviewRequest, db: Session = Depends(get_db)):
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).one_or_none()
    if pred is None:
        raise HTTPException(status_code=404, detail={"message": "Comment not found."})
    rec = Review(comment_id=pred.comment_id, prediction_id=pred.id, decision=body.decision, notes=body.notes)
    db.add(rec)
    db.commit()
    return {"ok": True, "decision": rec.decision}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    data = latest_analysis(db)
    if data is None:
        return {
            "ok": True,
            "empty": True,
            "stats": compute_comment_stats([]),
            "recent_high_risk": [],
            "model_status": model_status(),
        }
    highs = [c for c in data.get("comments") or [] if c.get("risk") in {"HIGH", "CRITICAL"}][:8]
    return {**data, "empty": False, "recent_high_risk": highs}


@router.get("/research/metrics")
def research_metrics():
    metrics = load_research_metrics()
    if metrics is None:
        return {"available": False, "message": "Requires training"}
    return {"available": True, "metrics": metrics}


@router.get("/research/errors")
def research_errors():
    from pathlib import Path
    from app.core.config import get_settings as _gs

    path = _gs().research_dir / "results" / "error_examples.json"
    if not path.exists():
        return {"available": False, "message": "Requires training"}
    return {"available": True, "errors": json.loads(path.read_text(encoding="utf-8"))}


@router.post("/live/start")
def live_start(body: LiveStartRequest):
    return manager.start(body.url)


@router.post("/live/pause")
def live_pause():
    return manager.pause()


@router.post("/live/resume")
def live_resume():
    return manager.resume()


@router.post("/live/stop")
def live_stop():
    return manager.stop()


@router.get("/live/status")
def live_status(poll: bool = Query(default=True)):
    if poll:
        return manager.poll()
    return manager.snapshot()


@router.get("/export/{analysis_id}/csv")
def export_csv(analysis_id: int, db: Session = Depends(get_db)):
    payload = serialize_analysis(db, analysis_id)
    return Response(comments_csv(payload), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=hifazat_analysis.csv"})


@router.get("/export/{analysis_id}/json")
def export_json(analysis_id: int, db: Session = Depends(get_db)):
    payload = serialize_analysis(db, analysis_id)
    return Response(comments_json(payload), media_type="application/json", headers={"Content-Disposition": "attachment; filename=hifazat_analysis.json"})


@router.get("/export/{analysis_id}/pdf")
def export_pdf(analysis_id: int, db: Session = Depends(get_db)):
    payload = serialize_analysis(db, analysis_id)
    return Response(comments_pdf(payload), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=hifazat_analysis.pdf"})


def _persist_env_var(key: str, value: str):
    env_path = get_settings().root_dir / ".env"
    example_path = get_settings().root_dir / ".env.example"
    lines: list[str] = []
    found = False

    if env_path.exists():
        source_text = env_path.read_text(encoding="utf-8")
    elif example_path.exists():
        source_text = example_path.read_text(encoding="utf-8")
    else:
        source_text = ""

    for line in source_text.splitlines():
        if line.strip().startswith(f"{key}=") or line.strip().startswith(f"export {key}="):
            lines.append(f"{key}={value}")
            found = True
        else:
            lines.append(line)
    if not found:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@router.get("/settings")
def get_app_settings():
    s = get_settings()
    raw_key = (s.youtube_api_key or "").strip()
    masked_key = ""
    if raw_key:
        if len(raw_key) > 8:
            masked_key = f"{raw_key[:4]}...{raw_key[-4:]}"
        else:
            masked_key = "****"

    return {
        "youtube_configured": bool(raw_key) and not s.force_demo_mode,
        "youtube_api_key_set": bool(raw_key),
        "youtube_api_key_masked": masked_key,
        "genai_configured": s.genai_enabled,
        "force_demo_mode": s.force_demo_mode,
        "high_confidence_threshold": high_threshold(),
        "low_confidence_threshold": low_threshold(),
        "model": model_status(),
    }


@router.post("/settings")
def update_settings(body: SettingsUpdate):
    if body.high_confidence_threshold is not None or body.low_confidence_threshold is not None:
        high = body.high_confidence_threshold if body.high_confidence_threshold is not None else high_threshold()
        low = body.low_confidence_threshold if body.low_confidence_threshold is not None else low_threshold()
        if low >= high:
            raise HTTPException(422, 'Review threshold must be below high-confidence threshold')
        set_thresholds(body.high_confidence_threshold, body.low_confidence_threshold)

    if body.youtube_api_key is not None:
        val = body.youtube_api_key.strip()
        _persist_env_var("YOUTUBE_API_KEY", val)
        if val:
            os.environ["YOUTUBE_API_KEY"] = val
        else:
            os.environ.pop("YOUTUBE_API_KEY", None)
        get_settings.cache_clear()

    if body.force_demo_mode is not None:
        val_str = "true" if body.force_demo_mode else "false"
        _persist_env_var("FORCE_DEMO_MODE", val_str)
        os.environ["FORCE_DEMO_MODE"] = val_str
        get_settings.cache_clear()

    return get_app_settings()
