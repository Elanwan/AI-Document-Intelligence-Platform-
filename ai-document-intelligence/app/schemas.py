from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Prediction(BaseModel):
    label: str
    confidence: float
    probabilities: dict[str, float]


class ValidationIssue(BaseModel):
    field: str
    severity: Literal["error", "warning"]
    message: str


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    sha256: str
    document_type: str
    classification_confidence: float
    field_confidence: float
    overall_confidence: float
    extracted_fields: dict
    validation_issues: list[dict]
    needs_review: bool
    review_status: str
    review_notes: str | None
    extraction_source: str
    created_at: datetime
    reviewed_at: datetime | None


class ReviewRequest(BaseModel):
    action: Literal["approve", "reject", "correct"]
    corrections: dict = Field(default_factory=dict)
    notes: str | None = Field(default=None, max_length=2000)


class HealthResponse(BaseModel):
    status: str
    classifier_ready: bool
    azure_openai_enabled: bool

