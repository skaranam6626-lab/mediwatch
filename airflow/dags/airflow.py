from datetime import datetime, timedelta
from airflow.utils.dates import days_ago
from airflow import DAG
from airflow.sensors.s3_key_sensor import S3KeySensor
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator
import os

default_args={
    'ownwer': 'airflow',
    'depends_on_past': False,
    'start_data': days_ago(1),
    'email_on_failure': False,
    'max_active_runs':1,
    'email_on_retry': False,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

from datetime import datetime
from airflow.decorators import dag
from airflow.operators.bash import BashOperator
from data_preprocessing_scripts.preprocessing import preprocess_data

@dag(
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["example"],
)
def my_simple_dag():
    # Define tasks
    runPreprocessing = PythonOperator(
        task_id="RunPreprocessing",
        poke_interval=10, # Check for file every 60s
        timeout=600, # timeout if file not found after 600s
        mode='poke',
        python_callable=preprocessing,
        DATA_PATH=os.getenv("DATA_PATH")
    )
    hello_task2 = BashOperator(
        task_id="say_hello2",
        bash_command="echo 'Hello from Airflow!2'",
    )
    hello_task3 = BashOperator(
        task_id="say_hello3",
        bash_command="echo 'Hello from Airflow!3'",
    )

# CRITICAL: You must instantiate the DAG at the top level
run_this_dag = my_simple_dag()


# dag = DAG(
#     'data-pipeline-example',
#     schedule_interval='@daily',
#     default_args=default_args,
#     catchup=False
# )

# #Task1 S3 sensor
# check_if_data_file_arrived= S3KeySensor(
#     task_id='check_if_file_arrived',
#     poke_interval=10, # Check for file every 60s
#     timeout=600, # timeout if file not found after 600s
#     bucket_key=S3_FILE_PATH,
#     bucket_name=BUCKET_NAME,
#     mode='poke',
#     dag=dag
# )

# # Task 2 Download the file locally
# download_file=PythonOperator(
#     task_id="download_file",
#     python_callable=download_file_from_s3,
#     op_kwargs={"access_key": os.environ["AWS_ACCESS_KEY_ID"], "secret_key": os.environ["AWS_SECRET_ACCESS_KEY"], "bucket_name": BUCKET_NAME, "file_name": S3_FILE_PATH, "local_file_path": os.path.join(LOCAL_REPO_PATH, RAW_FILE_NAME)},
#     provide_context=True,
#     dag=dag
# )

# #Python operator for preprocessing
# preprocess_task=PythonOperator(
#     task_id="preprocess_task",
#     python_callable=preprocess_data,
#     op_kwargs=={"input_path": os.path.join(LOCAL_REPO_PATH, RAW_FILE_NAME), "output_path": os.path.join(LOCAL_REPO_PATH, PREPROCESSED_FILE_NAME)},
#     provide_context=True,
#     dag=dag
# )

# # Bash operator dvc command
# dvc_commands_task=BashOperator(
#     task_id='dvc_commands_task',
#     bash_commands='cd ~ && dvc add *.csv && dvc commit -f && dvc push',
#     dag=dag
# )

# #Define task dependencies
# check_if_file_arrived >> download_file >> preprocess_task >> dvc_commands_task