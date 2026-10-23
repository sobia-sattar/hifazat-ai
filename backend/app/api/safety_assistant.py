from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.safety_assistant import ask_assistant, CRISIS_RESOURCES

router = APIRouter()


class AssistantChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    attached_context: dict[str, Any] | None = None


@router.post("/chat")
def chat_with_assistant(body: AssistantChatRequest):
    try:
        return ask_assistant(body.message, body.attached_context)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/crisis-resources")
def get_crisis_resources():
    return {
        "resources": CRISIS_RESOURCES,
        "notice": "If you or someone you know is in immediate danger, please reach out to emergency services or local crisis lines right away.",
    }
