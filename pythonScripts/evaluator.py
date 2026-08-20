"""Evaluate a trained model and gate deployment on metric thresholds."""

import json
import os
import sys
import logging

import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("evaluator")


def evaluate_model() -> dict:
    model_path = os.getenv("MODEL_FILE")
    data_path = os.getenv("PREPROCESSED_FILE_PATH")
    metrics_path = os.getenv("EVALUATION_METRICS_FILE")

    logger.info("Evaluating model at %s", model_path)
    model = joblib.load(model_path)

    df = pd.read_csv(data_path)
    y = df["readmitted"]
    X = df.drop("readmitted", axis=1)
    _, x_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    y_pred = model.predict(x_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, average="weighted")),
        "recall": float(recall_score(y_test, y_pred, average="weighted")),
        "f1": float(f1_score(y_test, y_pred, average="weighted")),
    }

    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("Evaluation metrics: %s", metrics)

    min_accuracy = float(os.getenv("MIN_ACCURACY", "0.50"))
    min_f1 = float(os.getenv("MIN_F1", "0.40"))

    if metrics["accuracy"] < min_accuracy:
        raise RuntimeError(
            f"Accuracy {metrics['accuracy']:.4f} below threshold {min_accuracy}"
        )
    if metrics["f1"] < min_f1:
        raise RuntimeError(f"F1 {metrics['f1']:.4f} below threshold {min_f1}")

    return metrics


if __name__ == "__main__":
    evaluate_model()
