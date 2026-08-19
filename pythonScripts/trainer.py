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
from monitor_utils import save_reference_data
from mlflow.models import ModelSignature
from mlflow.types.schema import Schema, ColSpec

logging.basicConfig(  
    filename='app.log', 
    filemode='a', # 'a' to append logs, 'w' to overwrite every run
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    level=logging.INFO # Capture INFO, WARNING, ERROR, and CRITICAL
    )
logger=logging.getLogger('trainer')

def create_signature_with_doubles(df: pd.DataFrame) -> ModelSignature:
    col_specs = []
    for col_name, dtype in df.dtypes.items():
        # Check if column is integer/long and map to double
        if pd.api.types.is_integer_dtype(dtype):
            col_specs.append(ColSpec("double", str(col_name)))
        else:
            # Infer standard mapping or let MLflow handle it
            mlflow_type = "string" if pd.api.types.is_string_dtype(dtype) else "double"
            col_specs.append(ColSpec(mlflow_type, str(col_name)))
            
    return ModelSignature(inputs=Schema(col_specs))

def loadAndPrepare(dataPath: str) -> tuple:
    logger.info(f"Loading data from {dataPath}")
    df=pd.read_csv(dataPath)
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
        save_reference_data(xtrain)
        model=trainModel(xtrain,ytrain, hyperparams)
        metrics=evaluateModel(model,xtest,ytest)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(sk_model=model, artifact_path="model", input_example=xtrain[0:3], signature=create_signature_with_doubles(xtrain))
        #Save the model locally
        #modelPath=f"{os.getenv('MODEL_STORE_PATH')}/mediwatch-{mlflow.active_run().info.run_id}.joblib"
        modelPath=f"{os.getenv('MODEL_FILE')}"
        os.makedirs(os.path.dirname(modelPath), exist_ok=True)
        import joblib
        joblib.dump(model, modelPath)
        logger.info(f"Model saved to {modelPath}")

if __name__ == '__main__':
    train()