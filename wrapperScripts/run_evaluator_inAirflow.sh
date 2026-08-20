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

export PREPROCESSED_FILE_PATH="$HOME_PATH/output/diabetic_data_processed.csv"
export MODEL_FILE="$HOME_PATH/output/mediwatch.joblib"
export EVALUATION_METRICS_FILE="$HOME_PATH/output/evaluation_metrics.json"
export MIN_ACCURACY="${MIN_ACCURACY:-0.50}"
export MIN_F1="${MIN_F1:-0.40}"

python3 pythonScripts/evaluator.py
