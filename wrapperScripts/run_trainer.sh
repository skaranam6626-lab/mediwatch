#!/bin/bash
set -e

if [ -z "$HOME_PATH" ]; then
    echo "HOME_PATH is not provided, so taking current dir. Ensure folder structure is maintained"
    HOME_PATH=`pwd`
fi

echo "📥 Running  Mediwatch dataset preprocessing..."
echo "HOME_PATH:$HOME_PATH"
cd $HOME_PATH


export PYTHONPATH=".:./pythonScripts"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/setup_env.sh"
setup_python_env

export PREPROCESSED_FILE_PATH=$HOME_PATH"/output/diabetic_data_processed.csv"
export MODEL_FILE=$HOME_PATH"/output/mediwatch.joblib"
export EXPERIMENT_NAME="MediWatch-PatientReadmission-1"
export N_ESTIMATORS=10
export MAX_DEPTH=10
export TRAINING_DATA_FILE=$HOME_PATH"/output/trainingData.csv"
export GIT_PYTHON_REFRESH=quiet

#Run mlflow in background (use python -m; Airflow task PATH may omit ~/.local/bin)
python3 pythonScripts/trainer.py
