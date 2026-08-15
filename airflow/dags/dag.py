from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator

DOCKERFILE_DIR='/opt/airflow/dag/'
IMAGE_TAG='trainer:latest'
default_args={
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026,1,1),
    'retries':1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    'launch_dockerfile_dag',
    default_args=default_args,
    description='Builds dockerfile and executes the resulting container',
    schedule_interval=None,
    catchup=False

)as dag

build_image=BashOperator(
    task_id='build_docker_image',
    bash_command=f'docker -f {DOCKERFILE} build -t {IMAGE_TAG}'
)