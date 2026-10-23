from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scam_detector import analyze_scam_text

router = APIRouter()


class ScamAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


@router.post("/analyze")
def analyze_scam(body: ScamAnalyzeRequest):
    try:
        return analyze_scam_text(body.text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
