# MediWatch User Manual

This manual explains how to install, configure, and run every part of the MediWatch patient readmission pipeline — from a first-time local setup through Docker, Airflow orchestration, and production-style deployment.

---

## Table of contents

1. [Overview](#1-overview)
2. [Tool dependencies](#2-tool-dependencies)
3. [Installation](#3-installation)
4. [Configuration](#4-configuration)
5. [Execution workflows](#5-execution-workflows)
6. [Web application guide](#6-web-application-guide)
7. [Airflow orchestration](#7-airflow-orchestration)
8. [Docker services](#8-docker-services)
9. [Outputs and artifacts](#9-outputs-and-artifacts)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

MediWatch predicts whether a diabetic patient is likely to be readmitted to hospital within 30 days, after 30 days, or not at all. The pipeline includes:

- **Data ingestion** from Kaggle
- **Preprocessing** (encoding, feature engineering)
- **Model training** (Random Forest + MLflow)
- **Hyperparameter tuning** (Ray Tune)
- **Evaluation & deployment** (metric gates + model promotion)
- **Drift monitoring** (Evidently)
- **Prediction webapp** (FastAPI)

![System architecture](./snapshots/architecture-diagram.png)

---

## 2. Tool dependencies

### Required software

| Tool | Minimum version | Purpose |
|---|---|---|
| **Python** | 3.10 | Core ML scripts and webapp |
| **pip** | Latest | Package management |
| **Docker** | 20.10+ | Containerized Airflow, MLflow, Ray, webapp |
| **Docker Compose** | v2+ | Multi-container orchestration |
| **curl** | Any | Dataset download |
| **unzip** | Any | Extract Kaggle zip |
| **Git** | Any | Clone repository |

### Python packages (`requirements.txt`)

| Package | Purpose |
|---|---|
| `fastapi`, `uvicorn` | Web application server |
| `scikit-learn` | Random Forest model |
| `pandas`, `numpy` | Data processing |
| `joblib` | Model serialization (`.joblib`) |
| `mlflow` | Experiment tracking and model registry |
| `ray[tune,data,client]==2.57.0` | Distributed hyperparameter tuning |
| `evidently` | Data drift detection |
| `imbalanced-learn` | SMOTE oversampling (optional trainer) |
| `matplotlib`, `seaborn` | EDA visualizations in preprocessing |
| `kaggle` | Dataset API client (optional; download uses curl) |

### Infrastructure services (via Docker)

| Service | Image | Port |
|---|---|---|
| MLflow | Custom (`dockerfile.mlflow`) | 5050 |
| Ray head | `rayproject/ray:2.57.0-py310` | 8265, 10001 |
| Ray worker | `rayproject/ray:2.57.0-py310` | — |
| Airflow webserver | Custom (`Dockerfile.airflow`) | 8080 |
| Airflow scheduler/worker | Custom | — |
| PostgreSQL | `postgres:13` | 5432 (internal) |
| Redis | `redis:latest` | 6379 (internal) |

---

## 3. Installation

### 3.1 Clone and set project root

```bash
git clone <repository-url> mediwatch
cd mediwatch
export HOME_PATH="$(pwd)"
```

### 3.2 Create Python virtual environment (local development)

Wrapper scripts create and manage a `.venv` automatically on first run. To set up manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Build Docker images (optional, for container workflows)

```bash
# Airflow (includes project requirements)
docker compose -f airflow/dockercompose-airflow build

# MLflow + Ray cluster
docker compose -f dockerScripts/dockercompose-raytune.yml build

# Standalone webapp
docker build -t mediwatch-webapp -f dockerScripts/dockerfile-mediwatch .
```

---

## 4. Configuration

### 4.1 `HOME_PATH`

All scripts resolve paths from `HOME_PATH`. Set it once per session:

```bash
export HOME_PATH="/path/to/mediwatch"
```

Inside Airflow containers, this is fixed to `/opt/airflow/mediwatch`.

### 4.2 Environment variables reference

| Variable | Default | Description |
|---|---|---|
| `HOME_PATH` | Current directory | Project root |
| `RAW_INPUT_FILE_PATH` | `$HOME_PATH/input/diabetic_data.csv` | Raw Kaggle CSV |
| `PREPROCESSED_FILE_PATH` | `$HOME_PATH/output/diabetic_data_processed.csv` | Model-ready data |
| `MODEL_FILE` | `$HOME_PATH/output/mediwatch.joblib` | Staging/serving model |
| `PRODUCTION_MODEL_FILE` | `$HOME_PATH/output/mediwatch_production.joblib` | Promoted production model |
| `TRAINING_DATA_FILE` | `$HOME_PATH/output/trainingData.csv` | Reference data for drift |
| `TRACK_INPUT_IN_FILE` | `$HOME_PATH/output/trackInputData.csv` | Live prediction inputs |
| `DRIFT_RESULTS_FILE` | `$HOME_PATH/output/driftResults.json` | Drift report output |
| `EVALUATION_METRICS_FILE` | `$HOME_PATH/output/evaluation_metrics.json` | Evaluation gate output |
| `EXPERIMENT_NAME` | `MediWatch-PatientReadmission-1` | MLflow experiment name |
| `N_ESTIMATORS` | `100` | Random Forest trees |
| `MAX_DEPTH` | `10` | Max tree depth |
| `MIN_ACCURACY` | `0.50` | Deployment gate: minimum accuracy |
| `MIN_F1` | `0.40` | Deployment gate: minimum F1 |
| `MLFLOW_TRACKING_URI` | `http://127.0.0.1:5050` | MLflow server URL |
| `RAY_ADDRESS` | `ray://127.0.0.1:10001` | Ray client connection |

### 4.3 Logging

All Python modules write to **`$HOME_PATH/app.log`**. Components logged:

- `trainer`, `tuner`, `evaluator`, `monitor`
- `clientApp`, `patientReadmissionPredictor`, `encodedValues`

---

## 5. Execution workflows

### 5.1 Full local pipeline (recommended first run)

Run these steps in order from the project root:

```bash
export HOME_PATH="$(pwd)"

# Step 1: Download data
./wrapperScripts/download.sh

# Step 2: Preprocess
./wrapperScripts/run_preprocessing.sh

# Step 3: Start MLflow + Ray (separate terminal or background)
docker compose -f dockerScripts/dockercompose-raytune.yml up -d --build

# Step 4: Train model
./wrapperScripts/run_trainer.sh

# Step 5 (optional): Hyperparameter tuning
./wrapperScripts/run_tuner.sh

# Step 6: Start webapp
./wrapperScripts/run_webApp.sh
```

**Expected outputs after a successful run:**

| File | Description |
|---|---|
| `input/diabetic_data.csv` | Raw dataset |
| `output/diabetic_data_processed.csv` | Encoded features |
| `output/mediwatch.joblib` | Trained model |
| `output/trainingData.csv` | Reference data for drift |
| `output/evaluation_metrics.json` | Metrics (if evaluator ran) |

### 5.2 SMOTE training (imbalanced classes)

```bash
./wrapperScripts/run_trainer_withSmote.sh
```

Output: `output/mediwatch_withSmote.joblib`

### 5.3 Drift monitoring only

```bash
./wrapperScripts/run_monitor.sh
cat output/driftResults.json
```

Requires `trainingData.csv` (from training) and `trackInputData.csv` (from webapp predictions).

### 5.4 Execution flow diagram

```
download.sh
    └─► run_preprocessing.sh
            └─► run_trainer.sh ──► mediwatch.joblib
                    └─► run_tuner.sh (optional, needs Ray)
                            └─► run_webApp.sh
                                    └─► /predict logs inputs
                                            └─► run_monitor.sh (drift check)
```

---

## 6. Web application guide

### 6.1 Start the webapp

```bash
./wrapperScripts/run_webApp.sh
# or via Docker:
docker build -t mediwatch-webapp -f dockerScripts/dockerfile-mediwatch .
docker run -p 8800:8800 mediwatch-webapp
```

### 6.2 Prediction UI

Open **http://127.0.0.1:8800/**

![Predictor UI](./snapshots/predictor-ui.png)

1. Fill in **Demographics** (race, gender, age)
2. Complete **Admission & Clinical** fields
3. Select **Diagnoses** (diag_1 required; diag_2/diag_3 optional)
4. Expand **Medications** section if needed (defaults to "No")
5. Click **Predict Readmission Risk**

**Result interpretation:**

| Display | Meaning |
|---|---|
| **High Risk** (red) | Readmission expected in less than 30 days |
| **Moderate Risk** (orange) | Readmission expected in more than 30 days |
| **Low Risk** (green) | No readmission expected |

Each prediction is appended to `output/trackInputData.csv` for drift monitoring.

### 6.3 Drift monitoring dashboard

Open **http://127.0.0.1:8800/monitoring**

![Monitoring UI](./snapshots/monitoring-ui.png)

- **Dataset Status** — overall drift detected or stable
- **Drifted Features** — count of features exceeding threshold
- **Drift Share** — percentage of features with drift
- **Feature table** — searchable, sortable per-feature scores

JSON API also available at **http://127.0.0.1:8800/monitoring/json**

### 6.4 REST API

**POST /predict** — submit patient record as JSON:

```bash
curl -X POST http://127.0.0.1:8800/predict \
  -H "Content-Type: application/json" \
  -d '{"race":"Caucasian","gender":"Female","age":"[50-60)", ...}'
```

Response:

```json
{"possibleReadmission": "No readmission expected."}
```

---

## 7. Airflow orchestration

### 7.1 Start Airflow

```bash
docker compose -f airflow/dockercompose-airflow up -d --build
```

UI: **http://127.0.0.1:8080/** — login `airflow` / `airflow`

Ensure the project is mounted at `/opt/airflow/mediwatch` (configured in `dockercompose-airflow`).

### 7.2 Available DAGs

| DAG ID | Schedule | Description |
|---|---|---|
| `mediwatch_ml_pipeline` | Weekly | Full lifecycle: ingest → train → evaluate → deploy → monitor → retrain on drift |
| `launch_mediwatch_trainer` | Manual | Download + train only |
| `launch_mediwatch_tuner` | Manual | Download + Ray Tune HPO |

### 7.3 Trigger the full ML pipeline

```bash
docker compose -f airflow/dockercompose-airflow exec airflow-scheduler \
  airflow dags trigger mediwatch_ml_pipeline
```

**Pipeline stages:**

1. **data_ingestion** — download + preprocess
2. **train_model** — Random Forest + MLflow logging
3. **evaluate_model** — accuracy ≥ 50%, F1 ≥ 40% gate
4. **deploy_model** — promote to `mediwatch_production.joblib`
5. **monitor_drift** — Evidently drift check
6. **check_retrain** — if drift detected → retrain branch

### 7.4 Airflow task → script mapping

| Airflow task | Wrapper script |
|---|---|
| `download_data` | `wrapperScripts/download.sh` |
| `preprocess_data` | `wrapperScripts/run_preprocessing_inAirflow.sh` |
| `train_model` | `wrapperScripts/run_trainer_inAirflow.sh` |
| `evaluate_model` | `wrapperScripts/run_evaluator_inAirflow.sh` |
| `deploy_model` | `wrapperScripts/run_deploy_inAirflow.sh` |
| `monitor_drift` | `wrapperScripts/run_monitor_inAirflow.sh` |

> **Note:** Airflow `BashOperator` commands must end with `;` when the command references a `.sh` file, otherwise Airflow treats the value as a Jinja template path.

### 7.5 Stop Airflow

```bash
docker compose -f airflow/dockercompose-airflow down
```

---

## 8. Docker services

### 8.1 MLflow + Ray (`dockercompose-raytune.yml`)

```bash
docker compose -f dockerScripts/dockercompose-raytune.yml up -d --build
```

| URL | Service |
|---|---|
| http://127.0.0.1:5050 | MLflow experiment tracking |
| http://127.0.0.1:8265 | Ray dashboard |
| ray://127.0.0.1:10001 | Ray client (for tuner) |

### 8.2 Webapp container

```bash
docker build -t mediwatch-webapp -f dockerScripts/dockerfile-mediwatch .
docker run -p 8800:8800 mediwatch-webapp
```

---

## 9. Outputs and artifacts

| Path | Created by | Description |
|---|---|---|
| `input/diabetic_data.csv` | download.sh | Raw Kaggle data |
| `output/diabetic_data_processed.csv` | preprocessing.py | Encoded feature matrix |
| `output/trainingData.csv` | trainer.py | Reference training split (drift baseline) |
| `output/mediwatch.joblib` | trainer.py | Staging model artifact |
| `output/mediwatch_production.joblib` | run_deploy_inAirflow.sh | Production-promoted model |
| `output/evaluation_metrics.json` | evaluator.py | accuracy, precision, recall, f1 |
| `output/driftResults.json` | monitor.py | Drift summary + per-feature scores |
| `output/trackInputData.csv` | webapp predictions | Live input log |
| `output/deployment.json` | run_deploy_inAirflow.sh | Deployment timestamp manifest |
| `app.log` | All Python modules | Application log file |
| `mlruns/` | MLflow (local) | Experiment runs (when using local MLflow) |

---

## 10. Troubleshooting

| Problem | Solution |
|---|---|
| Ray client timeout | Start Ray cluster: `docker compose -f dockerScripts/dockercompose-raytune.yml up -d` |
| MLflow 403 Invalid Host | Rebuild MLflow: `docker compose -f dockerScripts/dockercompose-raytune.yml up -d --build mlflow` |
| Airflow TemplateNotFound `.sh` | Ensure bash commands end with `;` in DAG files |
| Model not found in webapp | Run `./wrapperScripts/run_trainer.sh` first |
| Drift shows empty metrics | Ensure predictions exist in `trackInputData.csv` |
| Port in use | `lsof -i :8800` then kill the process |
| Airflow task fails on venv | Dependencies are baked into Airflow image; rebuild with `--build` |

For deeper technical details, see [CODE_REFERENCE.md](./CODE_REFERENCE.md) and [ARCHITECTURE.md](./ARCHITECTURE.md).

For a guided demo, see [VIDEO_WALKTHROUGH.md](./VIDEO_WALKTHROUGH.md).
