#!/bin/bash
set -e

if [ -z "$HOME_PATH" ]; then
    echo "HOME_PATH is not provided, so taking current dir. Ensure folder structure is maintained"
    HOME_PATH=`pwd`
fi

echo "📥 Running  Mediwatch dataset preprocessing..."
echo "HOME_PATH:$HOME_PATH"
cd $HOME_PATH


export PYTHONPATH=".:./pythonScripts"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/setup_env.sh"
setup_python_env

export GIT_PYTHON_REFRESH=quiet

#Run mlflow in background (use python -m; Airflow task PATH may omit ~/.local/bin)
python3 -m mlflow ui --port 5050 
#Command to kill mlflow server:kill -9 `lsof -i :5050| grep 'Python' | tr -s " " " " | cut -f2 -d" "`