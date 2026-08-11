import numpy as np
import pandas as pd
import joblib
import logging
import os

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

class_labels={
    "0":"in less than 30 days.",
    "1": "in more than 30 days.",
    "2": "No readmission expected."
}

class PatientReadmissionPredictor:
    """
        Load model    
    """
    def load_model(self):
        try:
            model=joblib.load(os.getenv("MODEL_FILE"))
            logger.info("Loaded model successfully")
            return model
        except Exception as e: 
            logger.info(f"{str(e)}")
            raise RuntimeError("Unable to load model")

    """
        Predict the outcome
    """
    def predict_patient_readmission(self,patientRecord):
        #for key, value in patientRecord.items():
        #    logger.info(f"Input: {key} {value}")
        
        #load model
        model=self.load_model()
        
        #Ensure input is as model expects in order
        patientRecordOrdered={}
        #logger.info(f"Model features:{model.feature_names_in_}")

        for key in model.feature_names_in_:
            patientRecordOrdered[key]=patientRecord[key]
        patientRecordDF = pd.DataFrame([patientRecordOrdered])
        result=model.predict(patientRecordDF)
        logger.info(f"Model result: {result}")
        return {"possibleReadmission": class_labels[str(result[0])]}

        