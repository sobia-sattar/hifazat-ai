from pydantic import BaseModel, Field


class TextAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    include_genai: bool = False
    safer_rephrase: bool = False


class YouTubeAnalyzeRequest(BaseModel):
    url: str = Field(min_length=8, max_length=500)
    max_comments: int = Field(default=200, ge=1, le=500)
    include_genai_summary: bool = True


class ReviewRequest(BaseModel):
    decision: str = Field(pattern="^(correct|incorrect|needs_review)$")
    notes: str = ""


class LiveStartRequest(BaseModel):
    url: str = Field(min_length=8, max_length=500)


class SettingsUpdate(BaseModel):
    high_confidence_threshold: float | None = Field(default=None, ge=0.5, le=0.99)
    low_confidence_threshold: float | None = Field(default=None, ge=0.2, le=0.8)
    youtube_api_key: str | None = None
    force_demo_mode: bool | None = None
