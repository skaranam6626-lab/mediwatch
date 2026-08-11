export PYTHONPATH=".:/Users/sk-training/main/src/mediwatch/data_preprocessing_scripts:/Users/sk-training/main/src/mediwatch/config"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

#Run pre-processing..
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
export RAW_INPUT_FILE_PATH=$HOME_PATH"/data/diabetic_data_raw.csv"
export PROCESSED_OUTPUT_FILE_PATH=$HOME_PATH"/data/diabetic_data_processed.csv"
python data_preprocessing_scripts/preprocessing.py

#Run mlflow at port:http://127.0.0.1:5050/
docker-compose -f dockerScripts/docker-compose.yml up -d mlflow 

#train the model...
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
export PROCESSED_OUTPUT_FILE_PATH=$HOME_PATH"/data/diabetic_data_processed.csv"
export MODEL_FILE=$HOME_PATH"/models/modelStore/mediwatch.joblib"
export EXPERIMENT_NAME="MediWatch-PatientReadmission-1"
export N_ESTIMATORS=100
export MAX_DEPTH=10
python3 models/scripts/train.py --data "$PROCESSED_OUTPUT_FILE_PATH" --experiment_name "$EXPERIMENT_NAME" --n_estimators "$N_ESTIMATORS" --max_depth "$MAX_DEPTH"

#Tune the model with Raytune

#Run the webapp at:http://127.0.0.1:8800/
export MODEL_FILE=$HOME_PATH"/models/modelStore/mediwatch.joblib"
python3 webapp/clientApp.py

#Run airflow at: http://127.0.0.1:8080/
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
docker compose -f airflow/dockerfile-airflow up -d
