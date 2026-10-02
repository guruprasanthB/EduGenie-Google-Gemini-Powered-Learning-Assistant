import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    environment: str
    gemini_api_key: str
    gemini_model: str
    gemini_fallback_model: str
    local_explanation_enabled: bool
    local_explanation_model: str
    max_input_chars: int


settings = Settings(
    app_name=os.getenv("APP_NAME", "EduGenie AI"),
    environment=os.getenv("ENVIRONMENT", "development"),
    gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
    gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip(),
    gemini_fallback_model=os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.8-flash").strip(),
    local_explanation_enabled=_as_bool(os.getenv("LOCAL_EXPLANATION_ENABLED")),
    local_explanation_model=os.getenv("LOCAL_EXPLANATION_MODEL", "llama3.2").strip(),
    max_input_chars=max(1000, int(os.getenv("MAX_INPUT_CHARS", "20000"))),
)