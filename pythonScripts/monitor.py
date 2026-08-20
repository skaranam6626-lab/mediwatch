from evidently import Report
from evidently.presets import DataDriftPreset
import pandas as pd
import json
import os
import logging

logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger("monitor")


def parse_evidently_snapshot(snapshot) -> dict:
    """Extract drift metrics from an Evidently 0.7+ Snapshot."""
    report_dict = snapshot.dict()
    metrics = report_dict.get("metrics", [])

    drift_summary = {
        "dataset_drift": False,
        "number_of_drifted_features": 0,
        "share_of_drifted_features": 0.0,
        "metrics_list": [],
    }

    for metric in metrics:
        metric_name = metric.get("metric_name", "")
        config = metric.get("config", {})
        value = metric.get("value")

        if "DriftedColumnsCount" in metric_name:
            if isinstance(value, dict):
                drift_summary["number_of_drifted_features"] = int(value.get("count", 0))
                drift_summary["share_of_drifted_features"] = float(value.get("share", 0.0))
                drift_share = config.get("drift_share", 0.5)
                drift_summary["dataset_drift"] = (
                    drift_summary["share_of_drifted_features"] >= drift_share
                )

        elif "ValueDrift" in metric_name:
            column = config.get("column", "")
            threshold = float(config.get("threshold", 0.1))
            drift_score = float(value) if value is not None else 0.0
            drift_summary["metrics_list"].append({
                "feature_name": column,
                "drift_score": drift_score,
                "drift_detected": drift_score >= threshold,
            })

    return drift_summary


def run_drift(
    output_path: str = os.getenv("DRIFT_RESULTS_FILE"),
    run_id: str = None,
) -> dict:
    """Run drift detection between reference and current data."""
    ref = pd.read_csv(os.getenv("TRAINING_DATA_FILE"))
    curr = pd.read_csv(os.getenv("TRACK_INPUT_IN_FILE"))

    report = Report(metrics=[DataDriftPreset()])
    snapshot = report.run(reference_data=ref, current_data=curr)

    drift_summary = parse_evidently_snapshot(snapshot)

    with open(output_path, "w") as f:
        json.dump(drift_summary, f, indent=2)
    logger.info(f"Drift summary saved to {output_path}")

    logger.info(f"Drift Summary:")
    logger.info(f"Dataset drift detected: {drift_summary.get('dataset_drift', 'Unknown')}")
    logger.info(f"Drifted features: {drift_summary.get('number_of_drifted_features', 0)}")
    logger.info(f"Drift percentage: {drift_summary.get('share_of_drifted_features', 0.0):.2%}")
    return drift_summary


if __name__ == "__main__":
    logger.info("Starting drift detection...")
    run_drift()
