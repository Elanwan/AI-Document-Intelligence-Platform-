from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    document_type: Mapped[str] = mapped_column(String(50), index=True)
    classification_confidence: Mapped[float] = mapped_column(Float)
    field_confidence: Mapped[float] = mapped_column(Float)
    overall_confidence: Mapped[float] = mapped_column(Float)
    extracted_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    validation_issues: Mapped[list] = mapped_column(JSON, default=list)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    review_status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_source: Mapped[str] = mapped_column(String(30), default="rules")
    raw_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

