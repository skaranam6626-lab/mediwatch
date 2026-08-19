# mediwatch

The automated pipeline performs these steps on every code change:

1. **Environment Setup**: Install dependencies
2. **Data Pipeline**: Download and preprocess Kaggle dataset
3. **Model Training**: Train model with MLflow tracking
4. **Artifact Storage**: Save models and experiment logs
5. **Quality Assurance**: Ensure reproducible results

**Workflow Triggers:**
- Push to main branch
- Pull requests
- Manual trigger

**What gets tracked:**
- Model performance metrics
- Training parameters
- Data preprocessing steps
- Model artifacts
---

## 📊 Model Performance Tracking

The pipeline tracks these metrics automatically:
- **Accuracy**: Overall prediction accuracy
- **Precision**: True positive rate
- **Recall**: Sensitivity
- **F1-Score**: Harmonic mean of precision and recall

All metrics are logged to MLflow for experiment comparison.


## Run below scripts to test the model 

$HOME_PATH : is uppermost parent directory of the project. Defaults to current directory. Ensure all child folders are under this directory.

All logs will be logged in app.log

##************* Run MediWatch from Command prompt***********************##########
# download the dataset
    export HOME_PATH="./mediwatch"
    cd $HOME_PATH
    ./wrapperScripts/download.sh

#run preprocessing: performs eda, feature engineering
    ./wrapperScripts/run_preprocessing.sh

#run mlflow and raytune in different containers
    docker compose -f dockerScripts/dockercompose-raytune.yml up -d

#run trainer
    ./wrapperScripts/run_trainer.sh

#run tuner
    ./wrapperScripts/run_tuner.sh

#run mediwatch from command prompt
    ./wrapperScripts/run_webApp.sh

##************* Run MediWatch from Docker container***********************##########
docker build -t mediwatch-webapp -f dockerScripts/dockerfile-mediwatch . && docker run -p 8800:8800 mediwatch-webapp
Model for prediction: http://127.0.0.1:8800/
Model Monitoring: http://127.0.0.1:8800/monitoring

##************* Run MediWatch Airflow container ***********************##########
docker compose -f airflow/dockercompose-airflow down && docker compose -f airflow/dockercompose-airflow up -d

Login airflow at: http://127.0.0.1:8080/
Run dag: launch_mediwatch_trainer

