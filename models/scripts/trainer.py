""" Simple ML training script with MLFLow integration"""

import argparse
import os
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import logging
from typing import Dict, Any
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score,f1_score 


logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)
objectCols=['race', 'gender', 'age', 'diag_1', 'diag_2', 'diag_3', 'metformin', 'repaglinide', 'nateglinide', 'chlorpropamide', 'glimepiride', 'acetohexamide', 'glipizide', 'glyburide', 'tolbutamide', 'pioglitazone', 'rosiglitazone', 'acarbose', 'miglitol', 'troglitazone', 'tolazamide', 'insulin', 'glyburide-metformin', 'glipizide-metformin', 'glimepiride-pioglitazone', 'metformin-rosiglitazone', 'metformin-pioglitazone', 'change', 'diabetesMed']


def loadAndPrepare(dataPath: str) -> tuple:
    logger.info(f"Loading data from {dataPath}")
    df=pd.read_csv(dataPath)
    # Remove objectCols:
    df=df.drop(columns=objectCols)

    y = df['readmitted']
    X = df.drop('readmitted', axis=1)
    return train_test_split(X,y, test_size=0.2, random_state=42)

def trainModel(xtrain: pd.DataFrame, ytrain: pd.Series, hyperparams: Dict[str, Any]) -> RandomForestClassifier:
    logger.info(f"Training with hyper params: {hyperparams}")

    model=RandomForestClassifier(
        n_estimators=hyperparams.get('n_estimators', 100),
        max_depth=hyperparams.get('max_depth', 10),
        min_samples_split=hyperparams.get('min_samples_split', 2),
        random_state=42
    )
    model.fit(xtrain,ytrain)
    return model

def evaluateModel(model: RandomForestClassifier, xtest: pd.DataFrame, ytest: pd.Series ) -> Dict[str, float]:
    ypred=model.predict(xtest)
    metrics = {
        'accuracy': accuracy_score(ytest, ypred),
        'precision': precision_score(ytest, ypred, average='weighted'),
        'recall': recall_score(ytest, ypred, average='weighted'),
        'f1': f1_score(ytest, ypred, average='weighted')
    }
    
    logger.info(f"Model metrics: {metrics}")
    return metrics

def train():
    # parser = argparse.ArgumentParser(description='Train fraud detection model')
    # parser.add_argument('--data', required=True, help='Path to training data')
    # parser.add_argument('--n_estimators', type=int, default=100)
    # parser.add_argument('--max_depth', type=int, default=10)
    # parser.add_argument('--min_samples_split', type=int, default=2)
    # parser.add_argument('--experiment_name', default=')

    #args = parser.parse_args()
    logger.info("Starting to train the model")
    #set mlflow
    mlflow_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://127.0.0.1:5050')
    n_estimators=int(os.getenv('N_ESTIMATORS','100'))
    max_depth=int(os.getenv('MAX_DEPTH','10'))
    min_samples_split=int(os.getenv('MIN_SAMPLES_SPLIT','2'))
    experiment_name=os.getenv('EXPERIMENT_NAME', 'MediWatch-PatientReadmission-1')
    dataPath=os.getenv('PREPROCESSED_FILE_PATH', '.')

    mlflow.set_tracking_uri(mlflow_uri)

    #Create or get experiment
    try:
        experiment_id=mlflow.create_experiment(experiment_name)
    except mlflow.exceptions.MlflowException:
        experiment_id=mlflow.get_experiment_by_name(experiment_name).experiment_id

    #Start mlflow run
    with mlflow.start_run(experiment_id=experiment_id):
        #log params
        hyperparams={
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'min_samples_split': min_samples_split 
        }
        mlflow.log_params(hyperparams)
        xtrain,xtest,ytrain, ytest=loadAndPrepare(dataPath)
        model=trainModel(xtrain,ytrain, hyperparams)
        metrics=evaluateModel(model,xtest,ytest)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(sk_model=model, name="model")
        #Save the model locally
        #modelPath=f"{os.getenv('MODEL_STORE_PATH')}/mediwatch-{mlflow.active_run().info.run_id}.joblib"
        modelPath=f"{os.getenv('MODEL_FILE')}"
        os.makedirs(os.path.dirname(modelPath), exist_ok=True)
        import joblib
        joblib.dump(model, modelPath)
        logger.info(f"Model saved to {modelPath}")

if __name__ == '__main__':
    train()