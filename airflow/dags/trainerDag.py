from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator

#DOCKERFILE_DIR='/opt/airflow/dag/'
#IMAGE_TAG='trainer:latest'

default_args={
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026,1,1),
    'retries':1,
    'retry_delay': timedelta(minutes=5)
}

def my_python_function():
    print("Hello from the Python script!")
    return "Python task completed"

with DAG(
    'launch_mediwatch_trainer',
    default_args=default_args,
    description='Builds dockerfile and executes the resulting container',
    schedule_interval=None,
    catchup=False
) as dag:

    downloadLatestFile=BashOperator(
        task_id='downloadLatestFile',
        env={ "HOME_PATH":"/opt/airflow/mediwatch"},
        bash_command='bash /opt/airflow/mediwatch/wrapperScripts/download.sh;',
    )
    
    run_trainer = BashOperator(
        task_id='run_trainer',
        env={ "HOME_PATH":"/opt/airflow/mediwatch"},
        bash_command='bash /opt/airflow/mediwatch/wrapperScripts/run_trainer_inAirflow.sh;'
    )

    # run_docker = DockerOperator(
    #     task_id='run_docker_image',
    #     image='',  # Replace with your Docker image
    #     api_version='auto',
    #     auto_remove=True,
    #     docker_url='unix://var/run/docker.sock',  # Standard macOS socket path
    #     network_mode='bridge',
    # )

    downloadLatestFile >> run_trainer