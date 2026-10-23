from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.incident_service import (
    create_incident_report,
    list_reports_for_reporter,
    delete_report_by_reporter,
    list_review_queue,
    update_report_status,
    submit_reviewer_feedback,
)

router = APIRouter()


class IncidentCreateRequest(BaseModel):
    platform: str = Field(default="other", max_length=64)
    incident_text: str = Field(min_length=1, max_length=4000)
    evidence_url: Optional[str] = Field(default=None, max_length=512)
    reporter_notes: Optional[str] = Field(default=None, max_length=1000)


class StatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(submitted|in_review|needs_info|actioned|dismissed|escalated)$")
    notes: str = Field(default="", max_length=1000)


class ReviewerFeedbackRequest(BaseModel):
    feedback: str = Field(pattern="^(agree|disagree|unsure)$")
    notes: str = Field(default="", max_length=1000)


@router.post("")
def submit_report(
    body: IncidentCreateRequest,
    x_reporter_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    return create_incident_report(
        db=db,
        platform=body.platform,
        incident_text=body.incident_text,
        evidence_url=body.evidence_url,
        reporter_notes=body.reporter_notes,
        reporter_token=x_reporter_token,
    )


@router.get("/my")
def get_my_reports(
    x_reporter_token: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    if not x_reporter_token:
        return []
    return list_reports_for_reporter(db, x_reporter_token)


@router.delete("/{report_id}")
def delete_my_report(
    report_id: int,
    x_reporter_token: str = Header(...),
    db: Session = Depends(get_db),
):
    delete_report_by_reporter(db, report_id, x_reporter_token)
    return {"ok": True, "message": "Incident report deleted."}


@router.get("/queue")
def get_queue(
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    return list_review_queue(db, status)


@router.patch("/{report_id}/status")
def patch_status(
    report_id: int,
    body: StatusUpdateRequest,
    db: Session = Depends(get_db),
):
    return update_report_status(db, report_id, body.status, body.notes)


@router.post("/{report_id}/feedback")
def post_feedback(
    report_id: int,
    body: ReviewerFeedbackRequest,
    db: Session = Depends(get_db),
):
    return submit_reviewer_feedback(db, report_id, body.feedback, body.notes)
