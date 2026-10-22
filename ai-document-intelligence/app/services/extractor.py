from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation


DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%b %d, %Y")


def _find(pattern: str, text: str, flags: int = re.IGNORECASE | re.MULTILINE) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def _date(value: str | None) -> str | None:
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return value.strip()


def _amount(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(Decimal(re.sub(r"[^0-9.\-]", "", value.replace(",", ""))))
    except (InvalidOperation, ValueError):
        return None


def _clean(fields: dict) -> dict:
    return {key: value for key, value in fields.items() if value not in (None, "")}


def extract_invoice(text: str) -> dict:
    currency = _find(r"\b(NZD|AUD|USD|EUR|GBP)\b", text)
    return _clean(
        {
            "supplier_name": _find(r"^(?:supplier|vendor|from)\s*:\s*(.+)$", text),
            "invoice_number": _find(r"(?:invoice\s*(?:number|no\.?|#))\s*[:#-]?\s*([A-Z0-9-]+)", text),
            "invoice_date": _date(_find(r"(?:invoice\s+date|date)\s*:\s*([^\n]+)", text)),
            "due_date": _date(_find(r"due\s+date\s*:\s*([^\n]+)", text)),
            "total_amount": _amount(
                _find(r"(?:grand\s+total|amount\s+due|total)\s*:\s*(?:NZ\$|AU\$|US\$|\$)?\s*([\d,]+\.\d{2})", text)
            ),
            "currency": currency or ("NZD" if "NZ$" in text else None),
        }
    )


def extract_bank_statement(text: str) -> dict:
    return _clean(
        {
            "account_name": _find(r"account\s+(?:name|holder)\s*:\s*(.+)$", text),
            "account_number": _find(r"account\s+(?:number|no\.?)\s*:\s*([\d-]+)", text),
            "statement_period": _find(r"statement\s+period\s*:\s*(.+)$", text),
            "opening_balance": _amount(_find(r"opening\s+balance\s*:\s*\$?\s*([\d,.-]+)", text)),
            "closing_balance": _amount(_find(r"closing\s+balance\s*:\s*\$?\s*([\d,.-]+)", text)),
            "currency": _find(r"\b(NZD|AUD|USD|EUR|GBP)\b", text) or ("NZD" if "NZ$" in text else None),
        }
    )


def extract_application_form(text: str) -> dict:
    return _clean(
        {
            "applicant_name": _find(r"(?:applicant|full)\s+name\s*:\s*(.+)$", text),
            "date_of_birth": _date(_find(r"(?:date\s+of\s+birth|dob)\s*:\s*([^\n]+)", text)),
            "email": _find(r"email\s*:\s*([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})", text),
            "phone": _find(r"(?:phone|mobile)\s*:\s*([+\d][\d ()-]{6,})", text),
            "address": _find(r"address\s*:\s*(.+)$", text),
        }
    )


EXTRACTORS = {
    "invoice": extract_invoice,
    "bank_statement": extract_bank_statement,
    "application_form": extract_application_form,
}


def extract_fields(document_type: str, text: str) -> dict:
    extractor = EXTRACTORS.get(document_type)
    return extractor(text) if extractor else {}

