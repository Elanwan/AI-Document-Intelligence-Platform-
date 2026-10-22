from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas


SAMPLES = {
    "invoice_sample.pdf": [
        "TAX INVOICE",
        "Supplier: North Shore Office Ltd",
        "Invoice Number: INV-2026-104",
        "Invoice Date: 2026-10-01",
        "Due Date: 2026-10-31",
        "Office equipment and delivery",
        "Total: NZ$ 1,249.50",
        "Currency: NZD",
    ],
    "bank_statement_sample.pdf": [
        "BANK STATEMENT",
        "Account Name: Jamie Chen",
        "Account Number: 12-3456-0789012-00",
        "Statement Period: 1 September 2026 to 30 September 2026",
        "Opening Balance: $2,150.20",
        "Closing Balance: $3,008.40",
        "Currency: NZD",
    ],
    "application_form_sample.pdf": [
        "APPLICATION FORM",
        "Applicant Name: Mia Thompson",
        "Date of Birth: 1994-06-12",
        "Email: mia.thompson@example.com",
        "Phone: +64 21 555 018",
        "Address: 20 Queen Street, Auckland",
    ],
    "incomplete_invoice_sample.pdf": [
        "INVOICE",
        "Supplier: Unknown Services",
        "Invoice Date: 2026-10-10",
        "Please arrange payment promptly.",
    ],
}


def create_pdf(path: Path, lines: list[str]) -> None:
    canvas = Canvas(str(path), pagesize=A4)
    _, height = A4
    text = canvas.beginText(72, height - 72)
    text.setFont("Helvetica", 12)
    for line in lines:
        text.textLine(line)
    canvas.drawText(text)
    canvas.save()


if __name__ == "__main__":
    output = Path(__file__).resolve().parent.parent / "data" / "samples"
    output.mkdir(parents=True, exist_ok=True)
    for name, content in SAMPLES.items():
        create_pdf(output / name, content)
    print(f"Created {len(SAMPLES)} sample PDFs in {output}")

