from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "HIFAZAT AI"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///./bullylens.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    youtube_api_key: str = ""
    youtube_oauth_access_token: str = ""
    youtube_owner_channel_id: str = ""
    genai_api_key: str = ""
    allow_external_explanations: bool = False
    genai_base_url: str = "https://api.openai.com/v1"
    genai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""

    feature_assistant_enabled: bool = True
    feature_scam_enabled: bool = True
    feature_reporting_enabled: bool = True
    feature_password_check_enabled: bool = True

    high_confidence_threshold: float = 0.75
    low_confidence_threshold: float = 0.55
    force_demo_mode: bool = False
    public_deployment: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def youtube_enabled(self) -> bool:
        return bool(self.youtube_api_key.strip()) and not self.force_demo_mode

    @property
    def genai_enabled(self) -> bool:
        return self.allow_external_explanations and bool(self.genai_api_key.strip())

    @property
    def root_dir(self) -> Path:
        return ROOT

    @property
    def models_dir(self) -> Path:
        return ROOT / "models"

    @property
    def data_dir(self) -> Path:
        return ROOT / "data"

    @property
    def research_dir(self) -> Path:
        return ROOT / "research"


@lru_cache
def get_settings() -> Settings:
    return Settings()
