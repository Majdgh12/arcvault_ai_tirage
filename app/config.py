from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None and value.strip():
            return value.strip()

    return default


def _get_csv(name: str, default: str) -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _resolve_path(raw_path: str | None, default_path: Path) -> Path:
    if not raw_path:
        return default_path

    candidate = Path(raw_path)
    return candidate if candidate.is_absolute() else BASE_DIR / candidate


@dataclass(slots=True)
class Settings:
    llm_provider: str
    gemini_api_key: str
    gemini_model: str
    use_mock_llm: bool
    llm_fallback_to_local: bool
    cors_origins: list[str]
    classification_prompt_path: Path
    extraction_prompt_path: Path
    output_file: Path
    fallback_queue: str
    escalation_queue: str
    confidence_threshold: float


def get_settings() -> Settings:
    return Settings(
        llm_provider="gemini",
        gemini_api_key=_get_first_env("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        gemini_model=_get_first_env("GEMINI_MODEL", default="gemini-2.5-flash"),
        use_mock_llm=_get_bool("USE_MOCK_LLM", False),
        llm_fallback_to_local=_get_bool("LLM_FALLBACK_TO_LOCAL", True),
        cors_origins=_get_csv(
            "CORS_ORIGINS",
            "http://localhost:8000,http://127.0.0.1:8000,http://localhost:5678,http://127.0.0.1:5678",
        ),
        classification_prompt_path=_resolve_path(
            os.getenv("CLASSIFICATION_PROMPT_PATH"),
            BASE_DIR / "prompts" / "classification_prompt.txt",
        ),
        extraction_prompt_path=_resolve_path(
            os.getenv("EXTRACTION_PROMPT_PATH"),
            BASE_DIR / "prompts" / "extraction_prompt.txt",
        ),
        output_file=_resolve_path(
            os.getenv("OUTPUT_FILE"),
            BASE_DIR / "outputs" / "triage_results.json",
        ),
        fallback_queue=os.getenv("FALLBACK_QUEUE", "Fallback Queue").strip(),
        escalation_queue=os.getenv("ESCALATION_QUEUE", "Escalation Queue").strip(),
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.7")),
    )


settings = get_settings()
