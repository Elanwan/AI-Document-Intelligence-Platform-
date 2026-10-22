from __future__ import annotations

import hashlib

from app.config import Settings
from app.models import Document
from app.services.azure_enhancer import enhance_fields
from app.services.classifier import DocumentClassifier
from app.services.extractor import extract_fields
from app.services.validator import validate_fields


def process_document(
    *, filename: str, content: bytes, text: str, classifier: DocumentClassifier, settings: Settings
) -> Document:
    prediction = classifier.predict(text)
    fields = extract_fields(prediction.label, text)
    fields, source = enhance_fields(settings, prediction.label, text, fields)
    issues, field_confidence = validate_fields(prediction.label, fields)
    overall = round(0.7 * prediction.confidence + 0.3 * field_confidence, 6)
    has_errors = any(issue["severity"] == "error" for issue in issues)
    needs_review = has_errors or overall < settings.review_threshold
    return Document(
        filename=filename,
        sha256=hashlib.sha256(content).hexdigest(),
        document_type=prediction.label,
        classification_confidence=prediction.confidence,
        field_confidence=field_confidence,
        overall_confidence=overall,
        extracted_fields=fields,
        validation_issues=issues,
        needs_review=needs_review,
        review_status="pending" if needs_review else "auto_accepted",
        extraction_source=source,
        raw_text=text,
    )

