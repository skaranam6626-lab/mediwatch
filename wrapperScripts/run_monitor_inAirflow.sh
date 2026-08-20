#!/bin/bash
set -e

if [ -z "$HOME_PATH" ]; then
    HOME_PATH="$(pwd)"
fi

echo "HOME_PATH: $HOME_PATH"
cd "$HOME_PATH"

export PYTHONPATH=".:./pythonScripts"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/setup_env.sh"
setup_python_env

export MODEL_FILE="$HOME_PATH/output/mediwatch.joblib"
export TRAINING_DATA_FILE="$HOME_PATH/output/trainingData.csv"
export TRACK_INPUT_IN_FILE="$HOME_PATH/output/trackInputData.csv"
export DRIFT_RESULTS_FILE="$HOME_PATH/output/driftResults.json"

python3 pythonScripts/monitor.py
