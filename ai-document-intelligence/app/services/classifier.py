from __future__ import annotations

import csv
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.config import get_settings
from app.schemas import Prediction


class DocumentClassifier:
    def __init__(self, model_path: Path | None = None, training_path: Path | None = None):
        settings = get_settings()
        self.model_path = model_path or settings.model_path
        self.training_path = training_path or settings.training_data_path
        self.pipeline: Pipeline | None = None

    @property
    def ready(self) -> bool:
        return self.pipeline is not None

    def train(self) -> None:
        texts: list[str] = []
        labels: list[str] = []
        with self.training_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                texts.append(row["text"])
                labels.append(row["label"])
        if len(set(labels)) < 2:
            raise ValueError("Training data must contain at least two classes")

        self.pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        ngram_range=(1, 2),
                        min_df=1,
                        sublinear_tf=True,
                        strip_accents="unicode",
                    ),
                ),
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
        self.pipeline.fit(texts, labels)

    def save(self) -> None:
        if self.pipeline is None:
            raise RuntimeError("Train the classifier before saving it")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, self.model_path)

    def load_or_train(self) -> None:
        if self.model_path.exists() and self.model_path.stat().st_mtime >= self.training_path.stat().st_mtime:
            self.pipeline = joblib.load(self.model_path)
            return
        self.train()
        self.save()

    def predict(self, text: str) -> Prediction:
        if self.pipeline is None:
            raise RuntimeError("Classifier is not ready")
        probabilities = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        by_class = {str(label): round(float(score), 6) for label, score in zip(classes, probabilities)}
        label = max(by_class, key=by_class.get)
        return Prediction(label=label, confidence=by_class[label], probabilities=by_class)


classifier = DocumentClassifier()
