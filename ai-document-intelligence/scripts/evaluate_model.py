from __future__ import annotations

import csv
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from app.config import get_settings  # noqa: E402
from app.services.classifier import DocumentClassifier  # noqa: E402


if __name__ == "__main__":
    rows = list(csv.DictReader(get_settings().training_data_path.open(encoding="utf-8")))
    train, test = train_test_split(rows, test_size=0.27, random_state=42, stratify=[row["label"] for row in rows])

    classifier = DocumentClassifier()
    # Fit the same pipeline on the split without writing a model artifact.
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    classifier.pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, strip_accents="unicode")),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42,
                    solver="liblinear",
                ),
            ),
        ]
    )
    classifier.pipeline.fit([r["text"] for r in train], [r["label"] for r in train])
    truth = [r["label"] for r in test]
    predicted = [classifier.predict(r["text"]).label for r in test]
    labels = sorted(set(truth))
    print("Holdout evaluation on synthetic data only; do not treat this as production accuracy.\n")
    print(classification_report(truth, predicted, labels=labels, zero_division=0))
    print("Labels:", labels)
    print("Confusion matrix:\n", confusion_matrix(truth, predicted, labels=labels))
