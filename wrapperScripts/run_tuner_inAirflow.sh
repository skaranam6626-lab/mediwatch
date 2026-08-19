#!/bin/bash
set -e

if [ -z "$HOME_PATH" ]; then
    echo "HOME_PATH is not provided, so taking current dir. Ensure folder structure is maintained"
    HOME_PATH=`pwd`
fi

echo "📥 Running  Mediwatch dataset preprocessing..."
echo "HOME_PATH:$HOME_PATH"
cd $HOME_PATH
echo "Current directory:`pwd`"

export PYTHONPATH=".:./pythonScripts"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/setup_env.sh"
setup_python_env requirements.txt


export PREPROCESSED_FILE_PATH=$HOME_PATH"/output/diabetic_data_processed.csv"
export EXPERIMENT_NAME="MediWatch-PatientReadmission-tuning-20260818"
export NUM_SAMPLES=2
export MAX_EPOCHS=2
export MLFLOW_ALLOW_FILE_STORE=true
export GIT_PYTHON_REFRESH=quiet
export MLFLOW_TRACKING_URI="${MLFLOW_TRACKING_URI:-http://127.0.0.1:5050}"
export RAY_ADDRESS="${RAY_ADDRESS:-ray://127.0.0.1:10001}"

echo "Waiting for Ray client at ${RAY_ADDRESS#ray://}..."
ray_host="${RAY_ADDRESS#ray://}"
ray_host="${ray_host%%:*}"
ray_port="${RAY_ADDRESS##*:}"
for i in $(seq 1 30); do
  if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('${ray_host}', ${ray_port})); s.close()" 2>/dev/null; then
    echo "Ray client is reachable."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Ray client not reachable. Start the cluster with:"
    echo "  docker compose -f dockerScripts/dockercompose-raytune.yml up -d"
    exit 1
  fi
  sleep 2
done

python3 -m mlflow ui --port 5050 &
python3 pythonScripts/tuner.py