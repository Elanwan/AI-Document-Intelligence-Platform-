from app.services.classifier import DocumentClassifier


def test_classifier_recognises_supported_document_types(tmp_path):
    classifier = DocumentClassifier(model_path=tmp_path / "model.joblib")
    classifier.train()

    examples = {
        "invoice": "TAX INVOICE Invoice Number: A-42 Supplier: Acme Total: NZ$ 125.00 Due Date: 2026-12-01",
        "bank_statement": "BANK STATEMENT Account Number: 12-3456-7890123-00 Statement Period: October Closing Balance: $900 NZD",
        "application_form": "APPLICATION FORM Applicant Name: Ana Lee Date of Birth: 1995-01-01 Email: ana@example.com Phone: 021 555 222",
    }
    for expected, text in examples.items():
        result = classifier.predict(text)
        assert result.label == expected
        assert 0 <= result.confidence <= 1
        assert abs(sum(result.probabilities.values()) - 1) < 0.00001


def test_classifier_model_can_be_saved_and_loaded(tmp_path):
    path = tmp_path / "classifier.joblib"
    first = DocumentClassifier(model_path=path)
    first.train()
    first.save()

    second = DocumentClassifier(model_path=path)
    second.load_or_train()
    assert second.ready
    assert second.predict("Invoice Number INV-8 Total 100 NZD").label == "invoice"

