To do: 
1. Correct pre-processing.py in pynb file
2. Check if model efficiency can be improved with different model types
3. 


Orchestrate model training and optimize hyperparameters using an orchestration system like Airflow. 
Execute parallel, large-scale experiments with an HPO tool such as RayTune.
Automate packaging, and deployment processes using CI/CD tools like Jenkins or orchestration tools such as Airflow.
Develop orchestration pipelines to retrain and deploy models based on drift detection.


export PYTHONPATH=".:./scripts"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

#Download data:
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
./scripts/download.sh

#Run pre-processing..
export RAW_INPUT_FILE_PATH=$HOME_PATH"/data/diabetic_data.csv"
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
export MODEL_FILE=$HOME_PATH"/output/mediwatch.joblib"
export EXPERIMENT_NAME="MediWatch-PatientReadmission-1"
export N_ESTIMATORS=100
export MAX_DEPTH=10
python3 scripts/trainer.py

#run preprocessing and training from docker
docker build -t mediwatch-webapp -f dockerScripts/dockerfile-mediwatch . && docker run -p 8800:8800 --name mediwatch-webapp mediwatch-webapp 
curl http://127.0.0.1:8800/preprocess
curl http://127.0.0.1:8800/train


#Tune the model with Raytune
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
docker compose -f dockerScripts/dockercompose-raytune.yml up -d



#Run the webapp at:http://127.0.0.1:8800/
export MODEL_FILE=$HOME_PATH"/output/mediwatch.joblib"
python3 webapp/clientApp.py

#Run airflow at: http://127.0.0.1:8080/
export HOME_PATH="/Users/sk-training/main/src/mediwatch"
docker compose -f airflow/dockercompose-airflow up -d

docker compose -f airflow/dockercompose-airflow down && docker compose -f airflow/dockercompose-airflow up -d

docker exec -it  /bin/bash

curl --url 'http://127.0.0.1:8800/predict' \
  -H 'Accept: */*' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Cache-Control: no-cache' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: application/json' \
  -b 'session=9ececbb0-33fc-452d-bee9-a4cae5af2391.4iNupMfp99y16AvWZ4IU1t7z8tg' \
  -H 'Origin: http://127.0.0.1:8800' \
  -H 'Pragma: no-cache' \
  -H 'Referer: http://127.0.0.1:8800/' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36' \
  -H 'sec-ch-ua: "Not=A?Brand";v="99", "Google Chrome";v="151", "Chromium";v="151"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  --data-raw '{"race":"AfricanAmerican","gender":"Male","age":"[10-20)","admission_type_id":4,"admission_source_id":1,"discharge_disposition_id":2,"num_lab_procedures":41,"num_medications":14,"num_procedures":0,"number_diagnoses":9,"number_emergency":0,"number_inpatient":1,"number_outpatient":1,"time_in_hospital":10,"diag_1":"131","diag_2":"131","diag_3":"117","metformin":"No","repaglinide":"No","nateglinide":"No","chlorpropamide":"No","glimepiride":"No","acetohexamide":"No","glipizide":"No","glyburide":"No","tolbutamide":"No","pioglitazone":"No","rosiglitazone":"No","acarbose":"No","miglitol":"No","troglitazone":"No","tolazamide":"No","insulin":"No","glyburide-metformin":"No","glipizide-metformin":"No","glimepiride-pioglitazone":"No","metformin-rosiglitazone":"No","metformin-pioglitazone":"No","change":"Ch","diabetesMed":"No"}'