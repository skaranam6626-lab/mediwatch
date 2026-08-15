#!/bin/bash
set -e

export PYTHONPATH=".:./data_preprocessing_scripts:./models/scripts"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt


echo "📥 Running  Mediwatch dataset preprocessing..."

if [ -z "$HOME_PATH" ]; then
    echo "HOME_PATH is not provided, so taking current dir. Ensure folder structure is maintained"
    HOME_PATH=`pwd`
fi

echo $HOME_PATH
export RAW_INPUT_FILE_PATH=$HOME_PATH"/data/diabetic_data.csv"
export PREPROCESSED_FILE_PATH=$HOME_PATH"/data/diabetic_data_processed.csv"


cd $HOME_PATH
python data_preprocessing_scripts/preprocessing.py