#!/bin/bash
set -e

export PYTHONPATH=".:./data_preprocessing_scripts:./models/scripts"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ -z "$HOME_PATH" ]; then
    echo "HOME_PATH is not provided, so taking current dir. Ensure folder structure is maintained"
    HOME_PATH=`pwd`
fi

echo $HOME_PATH
export PREPROCESSED_FILE_PATH=$HOME_PATH"/data/diabetic_data_processed.csv"
export MODEL_FILE=$HOME_PATH"/models/modelStore/mediwatch.joblib"
export EXPERIMENT_NAME="MediWatch-PatientReadmission-1"
export N_ESTIMATORS=100
export MAX_DEPTH=10

#Run mlflow in background
mlflow ui --port 5050 &
python3 models/scripts/trainer.py