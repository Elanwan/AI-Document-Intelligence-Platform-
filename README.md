# AI Document Intelligence Platform

A document intelligence project that runs locally. Upload a text-based PDF to classify the document, extract key fields, and apply deterministic validation. Results with low confidence or missing fields are routed to a human review queue. The system runs fully offline by default, with Azure OpenAI available as an optional enhancement.

## Implemented Features

- Document classification using scikit-learn TF-IDF + Logistic Regression: `invoice`, `bank_statement`, and `application_form`
- Text extraction with pypdf; scanned PDFs without text return a clear error (OCR is outside the current MVP scope)
- Rule-based field extraction, date and amount normalization, and required-field validation for each document type
- Separate tracking of classification confidence, field completeness, and a combined score
- A human review queue for low-confidence results or validation failures
- Review actions: approve, reject, and correct, with revalidation after corrections
- SQLAlchemy persistence with SQLite by default and PostgreSQL configurable through an environment variable
- Automatic FastAPI API documentation and a web interface that requires no build step
- Optional Azure OpenAI field completion; the system also runs without an API key
- Synthetic training data, four sample PDFs, a model evaluation script, and pytest tests

> Accuracy note: This repository makes no claims about production accuracy. `scripts/evaluate_model.py` evaluates only the small synthetic holdout set included in the repository; its results do not represent performance on real business data. Before deployment, evaluate the system and calibrate thresholds using de-identified, manually labeled data that matches the intended use case.

## Quick Start

Requires Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_sample_pdfs.py
uvicorn app.main:app --reload
```

Open:

- Web interface: <http://127.0.0.1:8000>
- Swagger API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/api/health>

Upload any of the PDFs generated in `data/samples/`. On first startup, the application automatically trains and saves the local classifier.

## Testing and Model Evaluation

```bash
pytest --cov=app
python scripts/evaluate_model.py
```

Tests cover classifier saving and loading, PDF parsing, field extraction and validation, the upload API, the review queue, manual corrections, rejection, and invalid input.

## API Examples

Upload a document:

```bash
curl -F "file=@data/samples/invoice_sample.pdf" http://127.0.0.1:8000/api/documents
```

List documents awaiting review:

```bash
curl "http://127.0.0.1:8000/api/reviews?status=pending"
```

Submit a manual correction:

```bash
curl -X PATCH http://127.0.0.1:8000/api/reviews/1 \
  -H "Content-Type: application/json" \
  -d '{"action":"correct","corrections":{"invoice_number":"INV-001","total_amount":250.0},"notes":"Verified"}'
```

## Configuration

Set the required variables from `.env.example` in your runtime environment. Key settings:

| Variable               | Default                   | Purpose                                                             |
| ---------------------- | ------------------------- | ------------------------------------------------------------------- |
| `DATABASE_URL`         | `sqlite:///./data/app.db` | SQLAlchemy database connection                                      |
| `REVIEW_THRESHOLD`     | `0.65`                    | Results with a combined score below this value require human review |
| `MAX_UPLOAD_MB`        | `10`                      | Maximum upload size in MB                                           |
| `AZURE_OPENAI_ENABLED` | `false`                   | Enable Azure OpenAI field completion                                |

To enable Azure, also configure `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_DEPLOYMENT`. The LLM only fills fields that the extraction rules did not capture. The same business validation rules still apply, and LLM output is not used as a probability-based confidence score.

## PostgreSQL / Docker

```bash
docker compose up --build
```

This configuration starts FastAPI and PostgreSQL 16. The default SQLite database is a lightweight option for development. For deployment, use PostgreSQL and store database and Azure credentials in a secrets management service.

## Processing Flow

```text
PDF upload
  -> text extraction
  -> ML document classification
  -> rule extraction
  -> optional Azure OpenAI field completion
  -> deterministic validation
  -> confidence + review decision
  -> SQLite/PostgreSQL
  -> auto accepted OR human review queue
```

The combined score is currently calculated as `0.7 * classification probability + 0.3 * field completeness`. Any required-field validation error also forces human review, so a high classification probability cannot bypass business validation.

## Project Structure

```text
app/
  main.py                 FastAPI routes and review API
  database.py             SQLite/PostgreSQL database configuration
  models.py               Persistence models
  services/
    classifier.py         Model training, saving, loading, and prediction
    pdf_text.py           PDF text extraction
    extractor.py          Rule-based field extraction and normalization
    validator.py          Deterministic business validation
    azure_enhancer.py     Optional Azure OpenAI enhancement
    processor.py          End-to-end processing orchestration
  static/                 Web interface
data/training_documents.csv
scripts/
tests/
```

## Next Steps for Production

- Add OCR, such as Azure AI Document Intelligence, to process scanned PDFs
- Replace synthetic training data with real labeled datasets and track model versions and experiment results
- Calibrate classification probabilities and set review thresholds for each document type
- Add authentication, role-based access control (RBAC), audit logs, data retention policies, and field-level encryption
- Use a background task queue for large files and add observability, rate limiting, and malicious file scanning
- Add database migrations with Alembic and object storage; the current example stores extracted text but does not retain the original PDFs


