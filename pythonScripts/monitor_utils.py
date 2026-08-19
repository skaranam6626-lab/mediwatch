import pandas as pd
import os

def save_reference_data(df):
    filepath=os.getenv('TRAINING_DATA_FILE')
    df.to_csv(filepath, index=False)


def append_input(record: dict):
    filepath=os.getenv('TRACK_INPUT_IN_FILE')
    df=pd.DataFrame([record])
    df.to_csv(filepath,mode='a',header=not os.path.exists(filepath), index=False) 