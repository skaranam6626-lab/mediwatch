# MediWatch — Patient Readmission ML Pipeline

MediWatch is an end-to-end machine learning pipeline that predicts hospital readmission risk for diabetic patients. It covers data ingestion, preprocessing, model training, hyperparameter tuning, experiment tracking, drift monitoring, and a prediction web app.

The automated CI/CD pipeline runs these steps on every code change:

1. **Environment setup** — install Python dependencies
2. **Data pipeline** — download and preprocess the Kaggle diabetes dataset
3. **Model training** — train a Random Forest classifier with MLflow tracking
4. **Artifact storage** — save models, metrics, and experiment logs
5. **Quality assurance** — ensure reproducible, tracked results

**Workflow triggers:** push to `main`, pull requests, manual trigger

---

## Project structure

```
mediwatch/
├── input/                  # Raw dataset (downloaded from Kaggle)
├── output/                 # Processed data, trained models, drift results
├── pythonScripts/          # Core ML scripts (preprocessing, trainer, tuner, monitor)
├── webapp/                 # FastAPI prediction and monitoring UI
├── wrapperScripts/         # Shell entry points for local, Docker, and Airflow runs
├── dockerScripts/          # Docker Compose and Dockerfiles (MLflow, Ray, webapp)
├── airflow/                # Airflow DAGs and Docker Compose for orchestration
├── requirements.txt        # Python dependencies (includes Ray 2.57.0)
└── app.log                 # Application log file (created at runtime)
```

---

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- `curl` and `unzip` (for dataset download)

---

## Configuration

### `HOME_PATH`

`HOME_PATH` is the root directory of the project. All wrapper scripts resolve file paths relative to it. If unset, scripts default to the current working directory.

```bash
export HOME_PATH="/path/to/mediwatch"
cd "$HOME_PATH"
```

### Logging

All Python scripts and the webapp write logs to **`app.log`** in the project root (`$HOME_PATH/app.log`). Logged components include:

- `trainer`, `tuner`, `monitor` (pythonScripts)
- `clientApp`, `patientReadmissionPredictor`, `encodedValues` (webapp)

Log level is `INFO` (captures INFO, WARNING, ERROR, and CRITICAL).

### Key environment variables

| Variable | Used by | Default / example |
|---|---|---|
| `HOME_PATH` | All wrapper scripts | Current directory |
| `RAW_INPUT_FILE_PATH` | Preprocessing | `$HOME_PATH/input/diabetic_data.csv` |
| `PREPROCESSED_FILE_PATH` | Trainer, tuner | `$HOME_PATH/output/diabetic_data_processed.csv` |
| `MODEL_FILE` | Trainer, webapp, monitor | `$HOME_PATH/output/mediwatch.joblib` |
| `EXPERIMENT_NAME` | Trainer, tuner | `MediWatch-PatientReadmission-1` |
| `N_ESTIMATORS`, `MAX_DEPTH` | Trainer | `10`, `10` |
| `NUM_SAMPLES`, `MAX_EPOCHS` | Tuner | `2`, `2` |
| `MLFLOW_TRACKING_URI` | Tuner | `http://127.0.0.1:5050` |
| `RAY_ADDRESS` | Tuner | `ray://127.0.0.1:10001` |
| `TRACK_INPUT_IN_FILE` | Webapp, monitor | `$HOME_PATH/output/trackInputData.csv` |
| `DRIFT_RESULTS_FILE` | Monitor | `$HOME_PATH/output/driftResults.json` |

---

## Run locally (command line)

All commands assume you are in the project root with `HOME_PATH` set:

```bash
export HOME_PATH="$(pwd)"
cd "$HOME_PATH"
```

### 1. Download the dataset

Downloads the Kaggle diabetes dataset into `input/`:

```bash
./wrapperScripts/download.sh
```

### 2. Preprocess data

Runs EDA, feature engineering, and encoding. Output: `output/diabetic_data_processed.csv`

```bash
./wrapperScripts/run_preprocessing.sh
```

### 3. Start MLflow and Ray Tune (Docker)

Start the MLflow tracking server and Ray cluster before training or tuning:

```bash
docker compose -f dockerScripts/dockercompose-raytune.yml up -d --build
```

| Service | URL |
|---|---|
| MLflow UI | http://127.0.0.1:5050/ |
| Ray Dashboard | http://127.0.0.1:8265/ |

To stop:

```bash
docker compose -f dockerScripts/dockercompose-raytune.yml down
```

Alternatively, run MLflow locally without Docker:

```bash
./wrapperScripts/run_mlflow.sh
```

### 4. Train the model

Trains a Random Forest and logs metrics to MLflow. Output: `output/mediwatch.joblib`

```bash
./wrapperScripts/run_trainer.sh
```

Train with SMOTE oversampling (for imbalanced classes):

```bash
./wrapperScripts/run_trainer_withSmote.sh
```

Output model: `output/mediwatch_withSmote.joblib`

### 5. Hyperparameter tuning (Ray Tune)

Requires the Ray cluster from step 3 to be running. The script waits up to 60 seconds for Ray on port `10001` before starting.

```bash
./wrapperScripts/run_tuner.sh
```

Tuning searches over `n_estimators`, `max_depth`, `min_samples_split`, and `min_samples_leaf`. Results are logged to MLflow and visible in the Ray dashboard.

### 6. Run drift monitoring

Compares current input data against training data using Evidently:

```bash
./wrapperScripts/run_monitor.sh
```

Output: `output/driftResults.json`

### 7. Start the prediction webapp

```bash
./wrapperScripts/run_webApp.sh
```

Open http://127.0.0.1:8800/ for predictions. Monitoring dashboard: http://127.0.0.1:8800/monitoring

---

## Run in Docker

### Webapp container

Builds a self-contained image with the trained model and serves the FastAPI app:

```bash
docker build -t mediwatch-webapp -f dockerScripts/dockerfile-mediwatch .
docker run -p 8800:8800 mediwatch-webapp
```

| Endpoint | URL |
|---|---|
| Predictions | http://127.0.0.1:8800/ |
| Monitoring | http://127.0.0.1:8800/monitoring |

---

## Run with Airflow

Start the Airflow cluster:

```bash
docker compose -f airflow/dockercompose-airflow up -d
```

Airflow UI: http://127.0.0.1:8080/ (default credentials: `airflow` / `airflow`)

Available DAGs:

| DAG | Description |
|---|---|
| `launch_mediwatch_trainer` | Download data → train model |
| `launch_mediwatch_tuner` | Download data → run Ray Tune hyperparameter search |

Trigger a DAG from the Airflow UI or CLI:

```bash
docker compose -f airflow/dockercompose-airflow exec airflow-scheduler \
  airflow dags trigger launch_mediwatch_trainer
```

Stop Airflow:

```bash
docker compose -f airflow/dockercompose-airflow down
```

---

## Model performance tracking

Metrics logged automatically to MLflow:

- **Accuracy** — overall prediction accuracy
- **Precision** — true positive rate
- **Recall** — sensitivity
- **F1-Score** — harmonic mean of precision and recall

Compare runs and download artifacts from the MLflow UI at http://127.0.0.1:5050/

---

## Wrapper scripts reference

| Script | Purpose |
|---|---|
| `download.sh` | Download Kaggle diabetes dataset |
| `run_preprocessing.sh` | Preprocess raw data |
| `run_trainer.sh` | Train Random Forest model |
| `run_trainer_withSmote.sh` | Train with SMOTE oversampling |
| `run_tuner.sh` | Hyperparameter tuning via Ray Tune |
| `run_monitor.sh` | Data drift detection |
| `run_webApp.sh` | Start prediction webapp |
| `run_mlflow.sh` | Start local MLflow UI |
| `run_trainer_inAirflow.sh` | Trainer variant for Airflow tasks |
| `run_tuner_inAirflow.sh` | Tuner variant for Airflow tasks |
| `setup_env.sh` | Shared venv setup (sourced by other scripts) |

---

## Troubleshooting

**Ray client connection timeout**

Ensure the Ray cluster is running and healthy before calling `run_tuner.sh`:

```bash
docker compose -f dockerScripts/dockercompose-raytune.yml ps
docker compose -f dockerScripts/dockercompose-raytune.yml logs ray-head
```

**MLflow 403 / Invalid Host header**

Rebuild the MLflow container after config changes:

```bash
docker compose -f dockerScripts/dockercompose-raytune.yml up -d --build mlflow
```

**Port already in use**

Find and stop the process using the port (example for MLflow on 5050):

```bash
kill -9 $(lsof -i :5050 | grep Python | awk '{print $2}')
```
