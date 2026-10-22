import pytest

from app.services.extractor import extract_fields
from app.services.pdf_text import PdfExtractionError, extract_pdf_text
from app.services.validator import validate_fields


def test_invoice_field_extraction_and_validation():
    text = """TAX INVOICE
Supplier: Harbour Design Ltd
Invoice Number: INV-900
Invoice Date: 2026-10-01
Due Date: 2026-10-31
Total: NZ$ 1,249.50
Currency: NZD
"""
    fields = extract_fields("invoice", text)
    issues, confidence = validate_fields("invoice", fields)
    assert fields["supplier_name"] == "Harbour Design Ltd"
    assert fields["invoice_number"] == "INV-900"
    assert fields["total_amount"] == 1249.50
    assert fields["invoice_date"] == "2026-10-01"
    assert issues == []
    assert confidence == 1.0


def test_missing_required_fields_trigger_errors():
    fields = extract_fields("invoice", "INVOICE\nSupplier: Example Ltd\nInvoice Date: 2026-10-01")
    issues, confidence = validate_fields("invoice", fields)
    assert {issue["field"] for issue in issues} == {"invoice_number", "total_amount"}
    assert confidence < 1


def test_pdf_text_extraction(pdf_factory):
    content = pdf_factory(["BANK STATEMENT", "Account Number: 12-3456-7890123-00"])
    text = extract_pdf_text(content)
    assert "BANK STATEMENT" in text
    assert "12-3456-7890123-00" in text


def test_rejects_non_pdf_content():
    with pytest.raises(PdfExtractionError, match="not a valid PDF"):
        extract_pdf_text(b"plain text")

