export PYTHONPATH=".:./data_preprocessing_scripts:./models/scripts"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

#Run pre-processing..
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
export RAW_INPUT_FILE_PATH=$HOME_PATH"/data/diabetic_data_raw.csv"
export PREPROCESSED_FILE_PATH=$HOME_PATH"/data/diabetic_data_processed.csv"
python data_preprocessing_scripts/preprocessing.py



#docker clean up:
docker container ls
docker exec -t <container-id> /bin/bash
docker rm <container-id>
docker rmi -f mediwatch-preprocessing-train:latest
docker-compose -f dockerScripts/docker-compose.yml down 



#Run mlflow at port:http://127.0.0.1:5050/
docker-compose -f dockerScripts/docker-compose.yml up -d mlflow 

#train the model...
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
export PREPROCESSED_FILE_PATH=$HOME_PATH"/data/diabetic_data_processed.csv"
export MODEL_FILE=$HOME_PATH"/models/modelStore/mediwatch.joblib"
export EXPERIMENT_NAME="MediWatch-PatientReadmission-1"
export N_ESTIMATORS=100
export MAX_DEPTH=10
python3 models/scripts/trainer.py

#run preprocessing and training from docker
docker build -t mediwatch-preprocessing-train -f dockerScripts/dockerfile-preprocessing . \ 
&& docker run -p 8811:8811 mediwatch-preprocessing-train 
curl http://127.0.0.1:8811/preprocess
curl http://127.0.0.1:8811/train




#Tune the model with Raytune

#Run the webapp at:http://127.0.0.1:8800/
export MODEL_FILE=$HOME_PATH"/models/modelStore/mediwatch.joblib"
python3 webapp/clientApp.py

#Run airflow at: http://127.0.0.1:8080/
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
docker compose -f airflow/dockerfile-airflow up -d
