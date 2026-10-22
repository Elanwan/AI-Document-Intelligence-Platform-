from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db, initialize_database
from app.models import Document
from app.schemas import DocumentResponse, HealthResponse, ReviewRequest
from app.services.classifier import classifier
from app.services.pdf_text import PdfExtractionError, extract_pdf_text
from app.services.processor import process_document
from app.services.validator import validate_fields


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    classifier.load_or_train()
    yield


app = FastAPI(
    title="AI Document Intelligence Platform",
    version="1.0.0",
    description="Classify PDFs, extract and validate fields, and route uncertain results to human review.",
    lifespan=lifespan,
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok" if classifier.ready else "starting",
        classifier_ready=classifier.ready,
        azure_openai_enabled=settings.azure_openai_enabled,
    )


@app.post("/api/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> Document:
    settings = get_settings()
    if file.content_type not in {"application/pdf", "application/x-pdf"} and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds the {settings.max_upload_mb} MB limit")
    try:
        text = extract_pdf_text(content)
        record = process_document(
            filename=file.filename or "document.pdf",
            content=content,
            text=text,
            classifier=classifier,
            settings=settings,
        )
    except PdfExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@app.get("/api/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    record = db.get(Document, document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return record


@app.get("/api/reviews", response_model=list[DocumentResponse])
def list_reviews(
    status: str | None = Query(default="pending"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[Document]:
    query = select(Document).where(Document.needs_review.is_(True)).order_by(Document.created_at.desc()).limit(limit)
    if status:
        query = query.where(Document.review_status == status)
    return list(db.scalars(query).all())


@app.patch("/api/reviews/{document_id}", response_model=DocumentResponse)
def review_document(document_id: int, request: ReviewRequest, db: Session = Depends(get_db)) -> Document:
    record = db.get(Document, document_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Document not found")

    record.review_notes = request.notes
    record.reviewed_at = datetime.now(timezone.utc)
    if request.action == "reject":
        record.review_status = "rejected"
        record.needs_review = False
    elif request.action == "approve":
        record.review_status = "approved"
        record.needs_review = False
    else:
        if not request.corrections:
            raise HTTPException(status_code=422, detail="Corrections are required for the correct action")
        fields = {**record.extracted_fields, **request.corrections}
        issues, field_confidence = validate_fields(record.document_type, fields)
        record.extracted_fields = fields
        record.validation_issues = issues
        record.field_confidence = field_confidence
        record.overall_confidence = round(0.7 * record.classification_confidence + 0.3 * field_confidence, 6)
        has_errors = any(issue["severity"] == "error" for issue in issues)
        record.needs_review = has_errors
        record.review_status = "corrected" if not has_errors else "pending"

    db.commit()
    db.refresh(record)
    return record

