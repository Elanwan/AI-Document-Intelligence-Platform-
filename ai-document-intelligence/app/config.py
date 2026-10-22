from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_url: str
    review_threshold: float
    max_upload_mb: int
    training_data_path: Path
    model_path: Path
    azure_openai_enabled: bool
    azure_openai_endpoint: str | None
    azure_openai_api_key: str | None
    azure_openai_deployment: str | None
    azure_openai_api_version: str


@lru_cache
def get_settings() -> Settings:
    threshold = float(os.getenv("REVIEW_THRESHOLD", "0.65"))
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("REVIEW_THRESHOLD must be between 0 and 1")

    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/app.db"),
        review_threshold=threshold,
        max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "10")),
        training_data_path=PROJECT_ROOT / "data" / "training_documents.csv",
        model_path=PROJECT_ROOT / "data" / "models" / "classifier.joblib",
        azure_openai_enabled=_as_bool(os.getenv("AZURE_OPENAI_ENABLED")),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )
