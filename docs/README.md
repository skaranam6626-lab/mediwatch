# MediWatch Documentation

Welcome to the MediWatch documentation hub. This folder contains the full technical and user-facing guides for the patient readmission ML pipeline.

## Documentation index

| Document | Description |
|---|---|
| [USER_MANUAL.md](./USER_MANUAL.md) | Step-by-step execution guide, tool dependencies, ports, and troubleshooting |
| [CODE_REFERENCE.md](./CODE_REFERENCE.md) | Module-by-module code documentation for every Python script, webapp component, and DAG |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design, data flow, orchestration, and deployment topology |
| [VIDEO_WALKTHROUGH.md](./VIDEO_WALKTHROUGH.md) | Recorded walkthrough script (use this to create a demo video) |

## Visual reference (snapshots)

| Snapshot | Description |
|---|---|
| [architecture-diagram.png](./snapshots/architecture-diagram.png) | End-to-end system architecture |
| [predictor-ui.png](./snapshots/predictor-ui.png) | Patient readmission predictor web UI |
| [monitoring-ui.png](./snapshots/monitoring-ui.png) | Data drift monitoring dashboard |

## Quick links

| Service | URL | Default credentials |
|---|---|---|
| Prediction webapp | http://127.0.0.1:8800/ | — |
| Drift monitoring | http://127.0.0.1:8800/monitoring | — |
| MLflow | http://127.0.0.1:5050/ | — |
| Ray Dashboard | http://127.0.0.1:8265/ | — |
| Airflow | http://127.0.0.1:8080/ | `airflow` / `airflow` |

## Recommended reading order

1. **USER_MANUAL.md** — if you want to run the pipeline end-to-end
2. **ARCHITECTURE.md** — if you want to understand how components connect
3. **CODE_REFERENCE.md** — if you want to modify or extend the codebase
4. **VIDEO_WALKTHROUGH.md** — if you want to record or watch a demo
