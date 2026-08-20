# MediWatch Code Reference

Module-by-module documentation for every Python script, webapp component, wrapper script, Airflow DAG, and Docker configuration file.

---

## Table of contents

1. [pythonScripts/](#1-pythonscripts)
2. [webapp/](#2-webapp)
3. [wrapperScripts/](#3-wrapperscripts)
4. [airflow/dags/](#4-airflow-dags)
5. [dockerScripts/](#5-dockerscripts)
6. [Configuration files](#6-configuration-files)

---

## 1. pythonScripts/

### `preprocessing.py`

**Purpose:** Transforms raw Kaggle diabetes CSV into a model-ready encoded dataset.

**Entry point:** `preprocess_data()` called from `if __name__ == "__main__"`

**Environment variables:**

| Variable | Description |
|---|---|
| `RAW_INPUT_FILE_PATH` | Input CSV path |
| `PREPROCESSED_FILE_PATH` | Output CSV path |

**Processing steps:**

1. Load raw CSV from `input/diabetic_data.csv`
2. Drop unused columns (`encounter_id`, `patient_nbr`, `weight`, etc.)
3. Encode categorical variables (race, gender, age brackets, medications, diagnoses)
4. Handle missing values and feature engineering
5. Write encoded DataFrame to `output/diabetic_data_processed.csv`

**Output columns:** Encoded numeric features + `readmitted` target column.

---

### `trainer.py`

**Purpose:** Train a Random Forest classifier, log experiment to MLflow, save model artifact.

**Entry point:** `train()` → called from `if __name__ == "__main__"`

**Key functions:**

| Function | Description |
|---|---|
| `loadAndPrepare(dataPath)` | Load CSV, split 80/20 train/test |
| `trainModel(xtrain, ytrain, hyperparams)` | Fit `RandomForestClassifier` |
| `evaluateModel(model, xtest, ytest)` | Compute accuracy, precision, recall, F1 |
| `create_signature_with_doubles(df)` | MLflow model signature for serving |
| `train()` | Orchestrates full training + MLflow logging |

**Environment variables:**

| Variable | Default | Description |
|---|---|---|
| `PREPROCESSED_FILE_PATH` | `.` | Training data CSV |
| `MODEL_FILE` | — | Output `.joblib` path |
| `EXPERIMENT_NAME` | `MediWatch-PatientReadmission-1` | MLflow experiment |
| `N_ESTIMATORS` | `100` | Number of trees |
| `MAX_DEPTH` | `10` | Max tree depth |
| `MIN_SAMPLES_SPLIT` | `2` | Min samples to split node |
| `MLFLOW_TRACKING_URI` | `http://127.0.0.1:5050` | MLflow server |

**Side effects:**

- Saves model to `MODEL_FILE`
- Saves training reference data via `monitor_utils.save_reference_data(xtrain)`
- Logs params, metrics, and sklearn model to MLflow

**Target classes:**

| Code | Label |
|---|---|
| 0 | Readmission in less than 30 days |
| 1 | Readmission in more than 30 days |
| 2 | No readmission expected |

---

### `trainer_withSmote.py`

**Purpose:** Identical to `trainer.py` but applies **SMOTE** (Synthetic Minority Over-sampling) via `imbalanced-learn` before training to address class imbalance.

**Output model:** `output/mediwatch_withSmote.joblib` (configured in wrapper script).

---

### `tuner.py`

**Purpose:** Hyperparameter optimization using **Ray Tune** with MLflow experiment logging.

**Entry point:** `main()`

**Key functions:**

| Function | Description |
|---|---|
| `loadData(dataPath)` | Load data, optionally subsample to 1000 records |
| `trainObjective(config, data, experiment_name)` | Ray Tune trial: train + log to MLflow |
| `main()` | Connect to Ray cluster, run `tune.Tuner` |

**Search space:**

| Parameter | Range |
|---|---|
| `n_estimators` | 50–200 |
| `max_depth` | 3–15 |
| `min_samples_split` | 2–10 |
| `min_samples_leaf` | 1–5 |

**Scheduler:** ASHA (Asynchronous Successive Halving)

**Environment variables:**

| Variable | Default | Description |
|---|---|---|
| `RAY_ADDRESS` | `ray://127.0.0.1:10001` | Ray client URL |
| `NUM_SAMPLES` | `100` | Number of trials |
| `MAX_EPOCHS` | `10` | ASHA max iterations |
| `MLFLOW_TRACKING_URI` | `http://127.0.0.1:5050` | MLflow server |

---

### `evaluator.py`

**Purpose:** Post-training evaluation gate. Validates model metrics against deployment thresholds.

**Entry point:** `evaluate_model()`

**Metrics computed:** accuracy, precision, recall, F1 (weighted)

**Thresholds (configurable):**

| Metric | Default threshold |
|---|---|
| `MIN_ACCURACY` | 0.50 |
| `MIN_F1` | 0.40 |

**Behavior:** Raises `RuntimeError` and exits with code 1 if thresholds are not met — blocking downstream deployment in Airflow.

**Output:** `output/evaluation_metrics.json`

---

### `monitor.py`

**Purpose:** Detect data drift between reference training data and live prediction inputs using **Evidently AI**.

**Entry point:** `run_drift()`

**Key functions:**

| Function | Description |
|---|---|
| `parse_evidently_snapshot(snapshot)` | Extract drift metrics from Evidently 0.7+ Snapshot |
| `run_drift(output_path)` | Run report, save JSON summary |

**Input files:**

| File | Role |
|---|---|
| `TRAINING_DATA_FILE` | Reference (baseline) distribution |
| `TRACK_INPUT_IN_FILE` | Current (production) inputs |

**Output structure (`driftResults.json`):**

```json
{
  "dataset_drift": true,
  "number_of_drifted_features": 32,
  "share_of_drifted_features": 0.8,
  "metrics_list": [
    {
      "feature_name": "admission_source_id",
      "drift_score": 0.83,
      "drift_detected": true
    }
  ]
}
```

---

### `monitor_utils.py`

**Purpose:** Helper utilities for drift monitoring data persistence.

| Function | Description |
|---|---|
| `save_reference_data(df)` | Write training reference CSV (`TRAINING_DATA_FILE`) |
| `append_input(record)` | Append single prediction record to `TRACK_INPUT_IN_FILE` |

Called by `trainer.py` (save reference) and `PatientReadmissionPredictor.py` (append live inputs).

---

### `mediwatch_preprocessing.ipynb`

**Purpose:** Jupyter notebook version of the preprocessing exploration (EDA, visualizations, encoding experiments). Used for development; production path uses `preprocessing.py`.

---

## 2. webapp/

### `clientApp.py`

**Purpose:** FastAPI application serving the prediction UI and drift monitoring dashboard.

**Routes:**

| Method | Path | Response | Description |
|---|---|---|---|
| `GET` | `/` | HTML (`index.html`) | Patient prediction form |
| `POST` | `/predict` | JSON | Run inference on submitted patient record |
| `GET` | `/monitoring` | HTML (`monitoring.html`) | Drift monitoring dashboard |
| `GET` | `/monitoring/json` | JSON | Drift results API |

**Dependencies:** `PatientReadmissionPredictor`, `encodedValues`, `monitor.run_drift`

**Server:** Uvicorn on `0.0.0.0:8800`

---

### `PatientReadmissionPredictor.py`

**Purpose:** Model inference wrapper.

**Class:** `PatientReadmissionPredictor`

| Method | Description |
|---|---|
| `load_model()` | Load `.joblib` from `MODEL_FILE` env var |
| `predict_patient_readmission(patientRecord)` | Order features, predict, log input, return label |

**Returns:**

```json
{"possibleReadmission": "No readmission expected."}
```

---

### `encodedValues.py`

**Purpose:** Maps UI categorical values to model feature names and integer encodings.

**Key data:** `encoded` dictionary — lookup tables for race, gender, age, medications, diagnoses, etc.

**Key function:** `get_encodedValue(key, value)` → `(modelFeatureName, encodedInteger)`

---

### `templates/index.html`

**Purpose:** Patient readmission prediction form UI.

**Sections:** Demographics, Admission & Clinical, Diagnoses, Medications (collapsible), Other.

**JavaScript:** Collects form data, POSTs JSON to `/predict`, renders risk badge (High/Moderate/Low).

---

### `templates/monitoring.html`

**Purpose:** Drift monitoring dashboard UI.

**Features:** Summary cards, feature drift table with search/filter/sort, color-coded drift badges.

---

## 3. wrapperScripts/

All wrapper scripts source `setup_env.sh` for environment bootstrapping.

### `setup_env.sh`

| Environment | Behavior |
|---|---|
| Docker / Airflow (`/.dockerenv` or `$AIRFLOW_HOME`) | Skip venv; use container Python |
| Local | Create/activate `.venv`, `pip install -r requirements.txt` |

### Script reference

| Script | Calls | Notes |
|---|---|---|
| `download.sh` | curl + unzip | Creates `input/` and `output/` dirs |
| `run_preprocessing.sh` | `preprocessing.py` | Local preprocessing |
| `run_preprocessing_inAirflow.sh` | `preprocessing.py` | Airflow variant |
| `run_trainer.sh` | `trainer.py` | Local training |
| `run_trainer_inAirflow.sh` | MLflow UI + `trainer.py` | Starts MLflow on :5050 in background |
| `run_trainer_withSmote.sh` | `trainer_withSmote.py` | SMOTE training |
| `run_tuner.sh` | `tuner.py` | Waits for Ray port 10001 |
| `run_tuner_inAirflow.sh` | MLflow UI + `tuner.py` | Airflow HPO variant |
| `run_evaluator_inAirflow.sh` | `evaluator.py` | Metric threshold gate |
| `run_deploy_inAirflow.sh` | shell cp + manifest | Promotes model to production |
| `run_monitor.sh` | `monitor.py` | Local drift check |
| `run_monitor_inAirflow.sh` | `monitor.py` | Airflow drift check |
| `run_webApp.sh` | `clientApp.py` | Starts webapp on :8800 |

---

## 4. airflow/dags/

### `ml_pipeline_dag.py` — `mediwatch_ml_pipeline`

**Schedule:** `@weekly`

**Task groups and tasks:**

| Task ID | Operator | Script |
|---|---|---|
| `start` | EmptyOperator | — |
| `data_ingestion.download_data` | BashOperator | `download.sh;` |
| `data_ingestion.preprocess_data` | BashOperator | `run_preprocessing_inAirflow.sh;` |
| `train_model` | BashOperator | `run_trainer_inAirflow.sh;` |
| `evaluate_model` | BashOperator | `run_evaluator_inAirflow.sh;` |
| `deploy_model` | BashOperator | `run_deploy_inAirflow.sh;` |
| `monitor_drift` | BashOperator | `run_monitor_inAirflow.sh;` |
| `check_retrain` | BranchPythonOperator | Reads `driftResults.json` |
| `retrain.*` | BashOperators | Full retrain chain on drift |
| `pipeline_complete` | EmptyOperator | — |

**Important:** All `bash_command` values end with `;` to prevent Airflow from treating them as Jinja template file paths.

---

### `trainerDag.py` — `launch_mediwatch_trainer`

**Schedule:** Manual (`None`)

**Flow:** `downloadLatestFile` → `run_trainer`

---

### `tunerDag.py` — `launch_mediwatch_tuner`

**Schedule:** Manual (`None`)

**Flow:** `downloadLatestFile` → `run_tuner`

---

## 5. dockerScripts/

### `dockercompose-raytune.yml`

| Service | Image | Ports | Role |
|---|---|---|---|
| `mlflow` | Custom | 5050 | Experiment tracking |
| `ray-head` | `rayproject/ray:2.57.0-py310` | 8265, 6379, 10001 | Ray cluster head |
| `ray-worker` | `rayproject/ray:2.57.0-py310` | — | Ray worker node |

### `dockerfile.mlflow`

Python 3.12 image with MLflow + boto3. Serves on `0.0.0.0:5050` with SQLite backend. Includes `--allowed-hosts "*"` for Docker network access.

### `dockerfile-mediwatch`

Python 3.12-slim image bundling the full project. Runs `webapp/clientApp.py` on port 8800.

### `airflow/Dockerfile.airflow`

Extends `apache/airflow:2.7.2`. Installs `requirements.txt` as the `airflow` user.

### `airflow/dockercompose-airflow`

Full Airflow cluster: PostgreSQL, Redis, webserver, scheduler, worker, triggerer, init. Mounts project at `/opt/airflow/mediwatch`.

---

## 6. Configuration files

### `requirements.txt`

Core Python dependencies. Pin: `ray[tune,data,client]==2.57.0`.

### `.github/workflows/ci-cd.yaml`

GitHub Actions workflow triggered on push/PR. Intended steps: checkout → install deps → download → preprocess → train.

> **Note:** Workflow currently references obsolete `scripts/` paths. Update to `wrapperScripts/` for CI to pass.

### `.gitignore`

Excludes `.venv/`, `__pycache__/`, `.DS_Store`, and other local artifacts.

---

## Logging convention

All modules use the same logging configuration:

```python
logging.basicConfig(
    filename='app.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO,
)
```

Logger names match module purpose: `trainer`, `tuner`, `evaluator`, `monitor`, `clientApp`, etc.
