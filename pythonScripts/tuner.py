import os
import pandas as pd
import numpy as np
import ray
import mlflow
import mlflow.sklearn
import logging
from ray import tune
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
from ray.tune.schedulers import ASHAScheduler



logging.basicConfig(    
    filename='app.log', 
    filemode='a', # 'a' to append logs, 'w' to overwrite every run
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO # Capture INFO, WARNING, ERROR, and CRITICAL
    )
logger=logging.getLogger('tuner')

def loadData(dataPath):
    logger.info(f"Loading data from {dataPath}")
    df=pd.read_csv(dataPath)
    max_records=1000
    y = df['readmitted']
    X = df.drop('readmitted', axis=1)
    if len(X) > max_records:
        X,_,y,_=train_test_split(X,y,train_size=max_records,random_state=43,stratify=y)
    return train_test_split(X,y, test_size=0.2, random_state=43)

def trainObjective(config, data=None, experiment_name=None):
    xtrain,xtest,ytrain,ytest=data
    model=RandomForestClassifier(
        n_estimators=config['n_estimators'],
        max_depth=int(config['max_depth']),
        min_samples_split=int(config['min_samples_split']),
        min_samples_leaf=int(config['min_samples_leaf']),
        random_state=42
    )
    model.fit(xtrain, ytrain)
    ypred=model.predict(xtest)
    #f1=f1_score(ytest,ypred, average='weighted')
    accuracy = accuracy_score(ytest, ypred)
    logger.info(f"trial config: {config}, accuracy:{accuracy}")

    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://127.0.0.1:5050')
    mlflow.set_tracking_uri(mlflow_uri)
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    else:
        experiment_id = experiment.experiment_id

    with mlflow.start_run(experiment_id=experiment_id):
        mlflow.log_params(config)
        #mlflow.log_metric("f1_score",f1)
        mlflow.log_metric("accuracy_score",accuracy)
        mlflow.sklearn.log_model(model, "model")
    #tune.report({"f1_score": f1})
    tune.report({"accuracy":accuracy})


def main():
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://127.0.0.1:5050')
    dataPath=os.getenv('PREPROCESSED_FILE_PATH', '.')
    num_samples=int(os.getenv('NUM_SAMPLES','100'))
    max_epochs=int(os.getenv('MAX_EPOCHS','10'))
    experiment_name=os.getenv('EXPERIMENT_NAME', 'MediWatch-PatientReadmission-tuning-1')

    mlflow.set_tracking_uri(mlflow_uri)
    try:
        experiment_id=mlflow.create_experiment(experiment_name)
    except mlflow.exceptions.MlflowException as ex:
        logger.info("unable to create experiment, in exception block", exc_info=ex)
        experiment_id=mlflow.get_experiment_by_name(experiment_name).experiment_id
    
    logger.info(f"----------------experiment_id:{experiment_id}------------")

    data=loadData(dataPath)
    if not ray.is_initialized():
        ray_address = os.getenv("RAY_ADDRESS", "ray://127.0.0.1:10001")
        logger.info(f"Connecting to Ray cluster at {ray_address}")
        ray.init(address=ray_address, ignore_reinit_error=True)
    
    search_space={
        'n_estimators': tune.randint(50, 200),
        'max_depth': tune.randint(3, 15),
        'min_samples_split': tune.randint(2, 10),
        'min_samples_leaf': tune.randint(1, 5)
    }

    scheduler=ASHAScheduler(
        time_attr='training_iteration',
        max_t=max_epochs,
        grace_period=1,
        reduction_factor=2
    )

    tuner = tune.Tuner(
        tune.with_parameters(trainObjective, data=data, experiment_name=experiment_name),
        param_space=search_space,
        tune_config=tune.TuneConfig(
            scheduler=scheduler,
            num_samples=num_samples,
            metric='accuracy',
            mode='max'
        )
    )

    results= tuner.fit()
    best_result=results.get_best_result(metric="accuracy", mode="max")
    logger.info(f"Best trial config: {best_result.config}")
    logger.info(f"Best trial final accuracy: {best_result.metrics}")

if __name__ == "__main__":
    main()

'''
python tuner.py --data "$DATA_PATH" --max_epochs "$MAX_EPOCHS" --num_samples "$NUM_SAMPLES" 
'''

    
