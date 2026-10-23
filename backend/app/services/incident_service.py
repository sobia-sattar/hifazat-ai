"""Incident Reporting & Review Service Layer."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.database.incident_models import IncidentReport, IncidentReportAudit, IncidentReviewFeedback

VALID_STATUSES = {"submitted", "in_review", "needs_info", "actioned", "dismissed", "escalated"}
VALID_FEEDBACK = {"agree", "disagree", "unsure"}


def generate_reporter_token() -> str:
    """Generate a high-entropy pseudo-random token for the reporter session."""
    return secrets.token_hex(24)


def create_incident_report(
    db: Session,
    platform: str,
    incident_text: str,
    evidence_url: str | None = None,
    reporter_notes: str | None = None,
    reporter_token: str | None = None,
) -> dict[str, Any]:
    token = reporter_token or generate_reporter_token()

    report = IncidentReport(
        reporter_token=token,
        platform=platform[:64],
        incident_text=incident_text[:4000],
        evidence_url=evidence_url[:512] if evidence_url else None,
        reporter_notes=reporter_notes[:1000] if reporter_notes else None,
        status="submitted",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Initial audit entry
    audit = IncidentReportAudit(
        report_id=report.id,
        old_status="none",
        new_status="submitted",
        notes="Incident report created by reporter.",
    )
    db.add(audit)
    db.commit()

    return {
        "id": report.id,
        "reporter_token": token,
        "status": report.status,
        "platform": report.platform,
        "created_at": report.created_at.isoformat(),
    }


def list_reports_for_reporter(db: Session, reporter_token: str) -> list[dict[str, Any]]:
    if not reporter_token:
        return []
    reports = db.query(IncidentReport).filter(IncidentReport.reporter_token == reporter_token).order_by(IncidentReport.id.desc()).all()
    return [
        {
            "id": r.id,
            "platform": r.platform,
            "incident_text": r.incident_text,
            "evidence_url": r.evidence_url,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]


def delete_report_by_reporter(db: Session, report_id: int, reporter_token: str) -> bool:
    report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found.")
    if report.reporter_token != reporter_token:
        raise HTTPException(status_code=403, detail="Unauthorized: You can only delete your own reports.")

    db.delete(report)
    db.commit()
    return True


def list_review_queue(db: Session, status_filter: str | None = None) -> list[dict[str, Any]]:
    query = db.query(IncidentReport)
    if status_filter and status_filter in VALID_STATUSES:
        query = query.filter(IncidentReport.status == status_filter)
    reports = query.order_by(IncidentReport.id.desc()).limit(100).all()

    return [
        {
            "id": r.id,
            "platform": r.platform,
            "incident_text": r.incident_text,
            "evidence_url": r.evidence_url,
            "reporter_notes": r.reporter_notes,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "audits": [
                {
                    "old_status": a.old_status,
                    "new_status": a.new_status,
                    "notes": a.notes,
                    "created_at": a.created_at.isoformat(),
                }
                for a in r.audits
            ],
            "feedbacks": [
                {
                    "feedback": f.feedback,
                    "reviewer_notes": f.reviewer_notes,
                    "created_at": f.created_at.isoformat(),
                }
                for f in r.feedbacks
            ],
        }
        for r in reports
    ]


def update_report_status(db: Session, report_id: int, new_status: str, notes: str) -> dict[str, Any]:
    if new_status not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of {sorted(VALID_STATUSES)}")

    report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found.")

    old = report.status
    report.status = new_status
    audit = IncidentReportAudit(
        report_id=report.id,
        old_status=old,
        new_status=new_status,
        notes=notes[:1000] if notes else "Status updated by reviewer.",
    )
    db.add(audit)
    db.commit()

    return {"ok": True, "id": report.id, "old_status": old, "new_status": new_status}


def submit_reviewer_feedback(db: Session, report_id: int, feedback: str, notes: str) -> dict[str, Any]:
    if feedback not in VALID_FEEDBACK:
        raise HTTPException(status_code=422, detail=f"Invalid feedback. Must be one of {sorted(VALID_FEEDBACK)}")

    report = db.query(IncidentReport).filter(IncidentReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Incident report not found.")

    rec = IncidentReviewFeedback(
        report_id=report.id,
        feedback=feedback,
        reviewer_notes=notes[:1000] if notes else "",
    )
    db.add(rec)
    db.commit()

    return {"ok": True, "id": report.id, "feedback": feedback}
