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



logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

def loadData(dataPath):
    df=pd.read_csv(dataPath)
    df=df.dropna(thresh=len(df)*0.5, axis=1).fillna(0)
    y = df['isFraud']
    X = df.drop('isFraud', axis=1)
    max_records=1000
    if len(X) > max_records:
        X,_,y,_=train_test_split(X,y,train_size=max_records,random_state=43,stratify=y)
    return train_test_split(X,y,test_size=.2,random_state=43)

def trainObjective(config, data=None,experiment_id=None):
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
    with mlflow.start_run(experiment_id=experiment_id):
        mlflow.log_params(config)
        #mlflow.log_metric("f1_score",f1)
        mlflow.log_metric("accuracy_score",accuracy)
        mlflow.sklearn.log_model(model, "model")
    #tune.report({"f1_score": f1})
    tune.report({"accuracy":accuracy})


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Tune fraud detection model')
    parser.add_argument('--data', required=True, help='Path to training data')
    parser.add_argument('--num_samples', type=int, default=20, help='Number of trials')
    parser.add_argument('--max_epochs', type=int, default=10, help='Max epochs per trial')
    parser.add_argument('--mlflow_uri', default='http://127.0.0.1:5050', help='MLflow URI')
    args = parser.parse_args()

    mlflow.set_tracking_uri(args.mlflow_uri)
    try:
        experiment_id=mlflow.create_experiment("fraud_detection_tuning_3")
    except mlflow.exceptions.MlflowException as ex:
        logger.info("unable to create experiment, in exception block", exc_info=ex)
        experiment_id=mlflow.get_experiment_by_name("fraud_detection_tuning_3").experiment_id
    
    logger.info(f"----------------experiment_id:{experiment_id}------------")

    data=loadData(args.data)
    if not ray.is_initialized():
        #runtime_env = {"pip": ["numpy==2.0.0"]} 
        ray.init(address='ray://127.0.0.1:10001')
    
    search_space={
        'n_estimators': tune.randint(50, 200),
        'max_depth': tune.randint(3, 15),
        'min_samples_split': tune.randint(2, 10),
        'min_samples_leaf': tune.randint(1, 5)
    }

    scheduler=ASHAScheduler(
        time_attr='training_iteration',
        max_t=args.max_epochs,
        grace_period=1,
        reduction_factor=2
    )

    tuner = tune.Tuner(
        tune.with_parameters(trainObjective, data=data, experiment_id=experiment_id),
        param_space=search_space,
        tune_config=tune.TuneConfig(
            scheduler=scheduler,
            num_samples=args.num_samples,
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
DATA_PATH="./data/sample_data.csv"
EXPERIMENT_NAME="fraud_detection_tuning"
MAX_EPOCHS=2
NUM_SAMPLES=1

python tune_ray.py --data "$DATA_PATH" --max_epochs "$MAX_EPOCHS" --num_samples "$NUM_SAMPLES" 
'''

    
