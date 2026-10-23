"""Database models for General Incident Reporting and Human Review.

Strict Privacy & Governance:
- Minimally collected incident reports.
- Full status lifecycle with immutable audit log records.
- Reviewer feedback stored for human review audit only; NEVER retrains ML models.
- Reporter token ensures users can query and delete only their own reports.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_token: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(64), default="other")
    incident_text: Mapped[str] = mapped_column(Text)
    evidence_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    reporter_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="submitted")  # submitted, in_review, needs_info, actioned, dismissed, escalated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    audits = relationship("IncidentReportAudit", back_populates="report", cascade="all, delete-orphan")
    feedbacks = relationship("IncidentReviewFeedback", back_populates="report", cascade="all, delete-orphan")


class IncidentReportAudit(Base):
    __tablename__ = "incident_report_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("incident_reports.id"), index=True)
    old_status: Mapped[str] = mapped_column(String(32))
    new_status: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report = relationship("IncidentReport", back_populates="audits")


class IncidentReviewFeedback(Base):
    __tablename__ = "incident_review_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("incident_reports.id"), index=True)
    feedback: Mapped[str] = mapped_column(String(32))  # agree, disagree, unsure
    reviewer_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report = relationship("IncidentReport", back_populates="feedbacks")
