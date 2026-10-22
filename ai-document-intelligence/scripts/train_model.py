import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.classifier import DocumentClassifier  # noqa: E402


if __name__ == "__main__":
    classifier = DocumentClassifier()
    classifier.train()
    classifier.save()
    print(f"Saved classifier to {classifier.model_path}")
