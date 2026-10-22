from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


class PdfExtractionError(ValueError):
    pass


def extract_pdf_text(content: bytes) -> str:
    if not content.startswith(b"%PDF"):
        raise PdfExtractionError("The uploaded file is not a valid PDF")
    try:
        reader = PdfReader(BytesIO(content))
        if reader.is_encrypted:
            raise PdfExtractionError("Password-protected PDFs are not supported")
        text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except PdfExtractionError:
        raise
    except Exception as exc:
        raise PdfExtractionError("The PDF could not be read") from exc
    if not text:
        raise PdfExtractionError(
            "No selectable text was found. This MVP does not include OCR; upload a text-based PDF."
        )
    return text

