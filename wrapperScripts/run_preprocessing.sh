#!/bin/bash
set -e

echo "📥 Running  Mediwatch dataset preprocessing..."

if [ -z "$HOME_PATH" ]; then
    echo "HOME_PATH is not provided, so taking current dir. Ensure folder structure is maintained"
    HOME_PATH=`pwd`
fi

echo "HOME_PATH:$HOME_PATH"
cd "$HOME_PATH"
echo "Current directory:`pwd`"

export PYTHONPATH=".:./pythonScripts"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/setup_env.sh"
setup_python_env

export RAW_INPUT_FILE_PATH=$HOME_PATH"/input/diabetic_data.csv"
export PREPROCESSED_FILE_PATH=$HOME_PATH"/output/diabetic_data_processed.csv"
python pythonScripts/preprocessing.py