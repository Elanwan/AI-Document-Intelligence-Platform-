from __future__ import annotations

import re
from datetime import date


REQUIRED_FIELDS = {
    "invoice": ("invoice_number", "invoice_date", "total_amount"),
    "bank_statement": ("account_number", "statement_period", "closing_balance"),
    "application_form": ("applicant_name", "email", "date_of_birth"),
}


def validate_fields(document_type: str, fields: dict) -> tuple[list[dict], float]:
    required = REQUIRED_FIELDS.get(document_type, ())
    issues: list[dict] = []
    present = 0
    for field in required:
        if fields.get(field) in (None, ""):
            issues.append({"field": field, "severity": "error", "message": "Required field is missing"})
        else:
            present += 1

    if document_type == "invoice" and fields.get("total_amount") is not None:
        if not isinstance(fields["total_amount"], (int, float)) or fields["total_amount"] <= 0:
            issues.append({"field": "total_amount", "severity": "error", "message": "Total must be greater than zero"})

    if document_type == "application_form":
        email = fields.get("email")
        if email and not re.fullmatch(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", str(email)):
            issues.append({"field": "email", "severity": "error", "message": "Email format is invalid"})
        dob = fields.get("date_of_birth")
        if dob:
            try:
                parsed = date.fromisoformat(str(dob))
                if parsed >= date.today():
                    issues.append({"field": "date_of_birth", "severity": "error", "message": "Date of birth must be in the past"})
            except ValueError:
                issues.append({"field": "date_of_birth", "severity": "warning", "message": "Date was not normalized to ISO format"})

    if document_type == "bank_statement":
        account = str(fields.get("account_number", ""))
        if account and len(re.sub(r"\D", "", account)) < 6:
            issues.append({"field": "account_number", "severity": "warning", "message": "Account number appears unusually short"})

    presence_score = present / len(required) if required else 0.0
    penalty = 0.15 * sum(issue["severity"] == "error" for issue in issues)
    penalty += 0.05 * sum(issue["severity"] == "warning" for issue in issues)
    return issues, round(max(0.0, min(1.0, presence_score - penalty)), 6)

