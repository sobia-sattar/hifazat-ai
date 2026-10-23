"""Channel-scoped human review. Model scores never trigger external actions."""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base


class ModerationComment(Base):
    __tablename__ = "moderation_comments"
    __table_args__ = (UniqueConstraint("youtube_comment_id", name="uq_moderation_comment"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_comment_id: Mapped[str] = mapped_column(String(128))
    video_id: Mapped[str] = mapped_column(String(64))
    channel_id: Mapped[str] = mapped_column(String(64), index=True)
    author_id: Mapped[str] = mapped_column(String(128), index=True)
    author_name: Mapped[str] = mapped_column(String(256))
    text: Mapped[str] = mapped_column(Text)
    flagged: Mapped[bool] = mapped_column(Boolean)
    decision: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ModerationAction(Base):
    __tablename__ = "moderation_actions"
    __table_args__ = (UniqueConstraint("comment_id", "action", name="uq_moderation_action"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    comment_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


def observe(db, video, raw_comments, predictions, demo=False):
    if demo:
        return
    for raw, prediction in zip(raw_comments, predictions):
        if not raw.get("author_id") or not raw.get("id") or not video.get("channel_id"):
            continue
        exists = db.query(ModerationComment).filter_by(youtube_comment_id=raw["id"]).first()
        if exists:
            if exists.text != raw['text']:
                exists.text = raw['text']
                exists.decision = 'pending'
                exists.flagged = prediction.get('binary_prediction') == 'HARMFUL'
            continue  # A repeated scan is not an additional strike.
        db.add(
            ModerationComment(
                youtube_comment_id=raw["id"],
                video_id=video["video_id"],
                channel_id=video["channel_id"],
                author_id=raw["author_id"],
                author_name=raw.get("author_name") or raw["author_id"],
                text=raw["text"],
                flagged=prediction.get("binary_prediction") == "HARMFUL",
            )
        )
    db.commit()
