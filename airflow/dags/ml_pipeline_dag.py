"""
MediWatch ML pipeline DAG: training, evaluation, deployment, and drift-triggered retraining.

Pipeline stages:
  1. Data ingestion  – download raw data, preprocess features
  2. Model training  – train Random Forest, log to MLflow
  3. Evaluation      – validate accuracy/F1 against thresholds
  4. Deployment      – promote model to production artifact path
  5. Monitoring      – run Evidently drift detection on live inputs
  6. Retraining      – if drift detected, re-run preprocess → train → evaluate → deploy
"""

import json
import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator
from airflow.utils.task_group import TaskGroup

HOME_PATH = "/opt/airflow/mediwatch"
WRAPPER = f"{HOME_PATH}/wrapperScripts"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

common_env = {
    "HOME_PATH": HOME_PATH,
    "MLFLOW_TRACKING_URI": os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5050"),
    "GIT_PYTHON_REFRESH": "quiet",
}


def should_retrain(**context) -> str:
    """Branch to retraining path when drift is detected."""
    drift_file = f"{HOME_PATH}/output/driftResults.json"
    with open(drift_file) as f:
        drift = json.load(f)

    if drift.get("dataset_drift"):
        share = drift.get("share_of_drifted_features", 0)
        print(
            f"Drift detected ({share:.0%} features drifted) — triggering retraining."
        )
        return "retrain.preprocess_for_retrain"

    print("No significant drift — pipeline complete.")
    return "pipeline_complete"


with DAG(
    dag_id="mediwatch_ml_pipeline",
    default_args=default_args,
    description="Train, evaluate, deploy, monitor, and retrain the MediWatch readmission model",
    schedule_interval="@weekly",
    catchup=False,
    tags=["mediwatch", "ml", "training", "deployment", "retraining"],
) as dag:

    start = EmptyOperator(task_id="start")
    pipeline_complete = EmptyOperator(task_id="pipeline_complete", trigger_rule="none_failed_min_one_success")

    # ── Stage 1: Data ingestion ──────────────────────────────────────────────
    with TaskGroup(group_id="data_ingestion") as data_ingestion:
        download_data = BashOperator(
            task_id="download_data",
            env=common_env,
            bash_command=f"bash {WRAPPER}/download.sh;",
        )

        preprocess_data = BashOperator(
            task_id="preprocess_data",
            env=common_env,
            bash_command=f"bash {WRAPPER}/run_preprocessing_inAirflow.sh;",
        )

        download_data >> preprocess_data

    # ── Stage 2: Training ──────────────────────────────────────────────────────
    train_model = BashOperator(
        task_id="train_model",
        env={
            **common_env,
            "EXPERIMENT_NAME": "MediWatch-PatientReadmission-pipeline",
            "N_ESTIMATORS": "100",
            "MAX_DEPTH": "10",
        },
        bash_command=f"bash {WRAPPER}/run_trainer_inAirflow.sh;",
    )

    # ── Stage 3: Evaluation ───────────────────────────────────────────────────
    evaluate_model = BashOperator(
        task_id="evaluate_model",
        env={
            **common_env,
            "MIN_ACCURACY": "0.50",
            "MIN_F1": "0.40",
        },
        bash_command=f"bash {WRAPPER}/run_evaluator_inAirflow.sh;",
    )

    # ── Stage 4: Deployment ───────────────────────────────────────────────────
    deploy_model = BashOperator(
        task_id="deploy_model",
        env=common_env,
        bash_command=f"bash {WRAPPER}/run_deploy_inAirflow.sh;",
    )

    # ── Stage 5: Drift monitoring ─────────────────────────────────────────────
    monitor_drift = BashOperator(
        task_id="monitor_drift",
        env=common_env,
        bash_command=f"bash {WRAPPER}/run_monitor_inAirflow.sh;",
    )

    check_retrain = BranchPythonOperator(
        task_id="check_retrain",
        python_callable=should_retrain,
    )

    # ── Stage 6: Retraining (triggered on drift) ──────────────────────────────
    with TaskGroup(group_id="retrain") as retrain:
        preprocess_for_retrain = BashOperator(
            task_id="preprocess_for_retrain",
            env=common_env,
            bash_command=f"bash {WRAPPER}/run_preprocessing_inAirflow.sh;",
        )

        retrain_model = BashOperator(
            task_id="retrain_model",
            env={
                **common_env,
                "EXPERIMENT_NAME": "MediWatch-PatientReadmission-retrain",
                "N_ESTIMATORS": "100",
                "MAX_DEPTH": "10",
            },
            bash_command=f"bash {WRAPPER}/run_trainer_inAirflow.sh;",
        )

        reevaluate_model = BashOperator(
            task_id="reevaluate_model",
            env={
                **common_env,
                "MIN_ACCURACY": "0.50",
                "MIN_F1": "0.40",
            },
            bash_command=f"bash {WRAPPER}/run_evaluator_inAirflow.sh;",
        )

        redeploy_model = BashOperator(
            task_id="redeploy_model",
            env=common_env,
            bash_command=f"bash {WRAPPER}/run_deploy_inAirflow.sh;",
        )

        preprocess_for_retrain >> retrain_model >> reevaluate_model >> redeploy_model

    # ── Pipeline wiring ───────────────────────────────────────────────────────
    start >> data_ingestion >> train_model >> evaluate_model >> deploy_model
    deploy_model >> monitor_drift >> check_retrain
    check_retrain >> retrain >> pipeline_complete
    check_retrain >> pipeline_complete
