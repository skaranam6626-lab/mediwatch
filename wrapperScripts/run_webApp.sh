#!/bin/bash
set -e
echo "📥 Starting WebApp for Mediwatch..."

if [ -z "$HOME_PATH" ]; then
    echo "HOME_PATH is not provided, so taking current dir. Ensure folder structure is maintained"
    HOME_PATH=`pwd`
fi

echo "HOME_PATH:$HOME_PATH"
cd "$HOME_PATH"

export PYTHONPATH=".:./pythonScripts"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/setup_env.sh"
setup_python_env

#Run the webapp at:http://127.0.0.1:8800/
export MODEL_FILE=$HOME_PATH"/output/mediwatch.joblib"
export TRACK_INPUT_IN_FILE=$HOME_PATH"/output/trackInputData.csv"
python3 webapp/clientApp.py