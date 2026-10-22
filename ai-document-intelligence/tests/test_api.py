def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["classifier_ready"] is True


def test_complete_invoice_is_processed(client, pdf_factory):
    pdf = pdf_factory(
        [
            "TAX INVOICE",
            "Supplier: North Shore Office Ltd",
            "Invoice Number: INV-2026-104",
            "Invoice Date: 2026-10-01",
            "Due Date: 2026-10-31",
            "Total: NZ$ 1,249.50",
            "Currency: NZD",
        ]
    )
    response = client.post("/api/documents", files={"file": ("invoice.pdf", pdf, "application/pdf")})
    assert response.status_code == 201
    body = response.json()
    assert body["document_type"] == "invoice"
    assert body["extracted_fields"]["invoice_number"] == "INV-2026-104"
    assert body["extracted_fields"]["total_amount"] == 1249.5
    assert body["validation_issues"] == []
    assert body["needs_review"] is False
    assert body["review_status"] == "auto_accepted"
    assert body["sha256"]


def test_incomplete_invoice_enters_review_queue_and_can_be_corrected(client, pdf_factory):
    pdf = pdf_factory(["INVOICE", "Supplier: Example Ltd", "Invoice Date: 2026-10-10", "Payment requested"])
    uploaded = client.post("/api/documents", files={"file": ("incomplete.pdf", pdf, "application/pdf")})
    assert uploaded.status_code == 201
    document = uploaded.json()
    assert document["needs_review"] is True
    assert document["review_status"] == "pending"

    queue = client.get("/api/reviews").json()
    assert [item["id"] for item in queue] == [document["id"]]

    corrected = client.patch(
        f"/api/reviews/{document['id']}",
        json={
            "action": "correct",
            "corrections": {"invoice_number": "INV-001", "total_amount": 250.0},
            "notes": "Verified against source document",
        },
    )
    assert corrected.status_code == 200
    result = corrected.json()
    assert result["review_status"] == "corrected"
    assert result["needs_review"] is False
    assert result["validation_issues"] == []


def test_reviewer_can_reject_document(client, pdf_factory):
    pdf = pdf_factory(["APPLICATION FORM", "Applicant Name: Pat Lee"])
    document = client.post("/api/documents", files={"file": ("form.pdf", pdf, "application/pdf")}).json()
    response = client.patch(f"/api/reviews/{document['id']}", json={"action": "reject", "notes": "Unreadable"})
    assert response.status_code == 200
    assert response.json()["review_status"] == "rejected"
    assert response.json()["needs_review"] is False


def test_non_pdf_upload_is_rejected(client):
    response = client.post("/api/documents", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 415


def test_unknown_document_returns_404(client):
    assert client.get("/api/documents/99999").status_code == 404
