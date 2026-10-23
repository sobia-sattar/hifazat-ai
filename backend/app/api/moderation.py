from collections import defaultdict
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.config import get_settings
from app.database.session import get_db
from app.services.moderation import ModerationComment, ModerationAction

router = APIRouter()
WARNING = "Please keep this conversation respectful. Personal attacks and harassment are not welcome. Further violations may result in your comments being removed from this channel."


def local_mutation(request: Request):
    if getattr(get_settings(), "public_deployment", False):
        raise HTTPException(403, "External moderation actions are disabled in the public deployment")
    origin = request.headers.get("origin")
    if origin and origin not in {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8011",
        "http://127.0.0.1:8011",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    }:
        raise HTTPException(403, "Cross-origin moderation request rejected")
    if request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(403, "Moderation is restricted to this local workstation")


@router.get("/status")
def status():
    s = get_settings()
    return dict(
        configured=bool(s.youtube_oauth_access_token and s.youtube_owner_channel_id),
        owner_channel_id=s.youtube_owner_channel_id or None,
        repeat_threshold=3,
        warning_template=WARNING,
        notice="Channel moderation only; cannot suspend an entire YouTube account. OAuth channel ownership is verified for each external action.",
    )


@router.get("/authors")
def authors(db: Session = Depends(get_db)):
    groups = defaultdict(list)
    for row in db.query(ModerationComment).order_by(ModerationComment.id.desc()).all():
        groups[(row.channel_id, row.author_id)].append(row)
    result = []
    for (channel, author), rows in groups.items():
        confirmed = sum(r.decision == "harmful" for r in rows)
        result.append(
            dict(
                author_id=author,
                channel_id=channel,
                name=rows[0].author_name,
                total=len(rows),
                flagged=sum(r.flagged for r in rows),
                confirmed=confirmed,
                repeat=confirmed >= 3,
                comments=[
                    dict(
                        id=r.id,
                        text=r.text,
                        video_id=r.video_id,
                        flagged=r.flagged,
                        decision=r.decision,
                        youtube_url=f"https://www.youtube.com/watch?v={r.video_id}&lc={r.youtube_comment_id}",
                    )
                    for r in rows
                ],
            )
        )
    return dict(
        authors=sorted(result, key=lambda r: (r["confirmed"], r["flagged"]), reverse=True),
        actions=[
            dict(
                id=a.id, comment_id=a.comment_id, action=a.action, status=a.status, created_at=a.created_at.isoformat()
            )
            for a in db.query(ModerationAction).order_by(ModerationAction.id.desc()).limit(50)
        ],
    )


class Review(BaseModel):
    decision: str = Field(pattern="^(harmful|safe|pending)$")


@router.post("/comments/{comment_id}/review", dependencies=[Depends(local_mutation)])
def review(comment_id: int, body: Review, db: Session = Depends(get_db)):
    row = db.get(ModerationComment, comment_id)
    if not row:
        raise HTTPException(404, "Comment not found")
    row.decision = body.decision
    db.commit()
    return {"ok": True}


class Action(BaseModel):
    action: str = Field(pattern="^(warn|reject|ban_author)$")
    confirmed: bool = False
    message: str = Field(default=WARNING, min_length=1, max_length=1000)


def youtube_request(client, method, path, **kwargs):
    response = client.request(method, "https://www.googleapis.com/youtube/v3/" + path, **kwargs)
    if response.status_code >= 400:
        raise HTTPException(
            502,
            "YouTube rejected the request. Check OAuth expiry, channel ownership, permissions and quota. No success is recorded.",
        )
    return response.json() if response.content else {}


@router.post("/comments/{comment_id}/action", dependencies=[Depends(local_mutation)])
def action(comment_id: int, body: Action, db: Session = Depends(get_db)):
    if not body.confirmed:
        raise HTTPException(422, "Explicit confirmation is required")
    row = db.get(ModerationComment, comment_id)
    if not row or row.decision != "harmful":
        raise HTTPException(409, "Review and confirm this comment as harmful first")
    settings = get_settings()
    if not settings.youtube_oauth_access_token or row.channel_id != settings.youtube_owner_channel_id:
        raise HTTPException(403, "Owner OAuth connection for this channel is required")
    if body.action == "ban_author":
        count = (
            db.query(ModerationComment)
            .filter_by(channel_id=row.channel_id, author_id=row.author_id, decision="harmful")
            .count()
        )
        if count < 3:
            raise HTTPException(409, "Channel blocking requires three distinct human-confirmed harmful comments")
    if body.action == "warn" and not body.message.strip():
        raise HTTPException(422, "Warning text cannot be blank")
    previous = db.query(ModerationAction).filter_by(comment_id=row.id, action=body.action).first()
    if previous and previous.status != "failed":
        raise HTTPException(409, "This action was already submitted; inspect the audit log and YouTube before retrying")
    if previous:
        changed = (
            db.query(ModerationAction)
            .filter_by(id=previous.id, status="failed")
            .update({"status": "pending", "message": body.message if body.action == "warn" else ""})
        )
        if changed != 1:
            db.rollback()
            raise HTTPException(409, "Action is already in progress")
        audit = previous
    else:
        audit = ModerationAction(
            comment_id=row.id, action=body.action, message=body.message if body.action == "warn" else ""
        )
        db.add(audit)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Action is already recorded") from exc
    mutation_started = False
    try:
        with httpx.Client(
            timeout=20, headers={"Authorization": "Bearer " + settings.youtube_oauth_access_token}
        ) as client:
            channels = youtube_request(client, "GET", "channels", params={"part": "id", "mine": "true"})
            if row.channel_id not in {c["id"] for c in channels.get("items", [])}:
                raise HTTPException(403, "OAuth identity does not own this channel")
            videos = youtube_request(client, "GET", "videos", params={"part": "snippet", "id": row.video_id})
            comments = youtube_request(
                client,
                "GET",
                "comments",
                params={"part": "snippet", "id": row.youtube_comment_id, "textFormat": "plainText"},
            )
            video = next(iter(videos.get("items", [])), {})
            comment = next(iter(comments.get("items", [])), {}).get("snippet", {})
            if (
                video.get("snippet", {}).get("channelId") != row.channel_id
                or comment.get("authorChannelId", {}).get("value") != row.author_id
                or comment.get("videoId") != row.video_id
            ):
                raise HTTPException(409, "Current YouTube comment identity could not be verified")
            if (comment.get("textOriginal") or comment.get("textDisplay")) != row.text:
                raise HTTPException(
                    409, "Comment text changed or is unavailable. Reassess it on YouTube; no action was submitted."
                )
            mutation_started = True
            if body.action == "warn":
                youtube_request(
                    client,
                    "POST",
                    "comments",
                    params={"part": "snippet"},
                    json={"snippet": {"parentId": row.youtube_comment_id, "textOriginal": body.message}},
                )
            else:
                youtube_request(
                    client,
                    "POST",
                    "comments/setModerationStatus",
                    params={
                        "id": row.youtube_comment_id,
                        "moderationStatus": "rejected",
                        "banAuthor": str(body.action == "ban_author").lower(),
                    },
                )
        audit.status = "succeeded"
        db.commit()
    except (httpx.HTTPError, HTTPException) as exc:
        audit.status = "uncertain" if mutation_started else "failed"
        db.commit()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(502, "Network error. Check the audit log and YouTube before retrying.") from exc
    return {"ok": True, "action": body.action, "scope": "owned channel only"}
