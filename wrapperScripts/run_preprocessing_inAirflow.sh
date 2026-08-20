#!/bin/bash
set -e

if [ -z "$HOME_PATH" ]; then
    HOME_PATH="$(pwd)"
fi

echo "HOME_PATH: $HOME_PATH"
cd "$HOME_PATH"

export PYTHONPATH=".:./pythonScripts"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "$SCRIPT_DIR/setup_env.sh"
setup_python_env

export RAW_INPUT_FILE_PATH="$HOME_PATH/input/diabetic_data.csv"
export PREPROCESSED_FILE_PATH="$HOME_PATH/output/diabetic_data_processed.csv"

python3 pythonScripts/preprocessing.py
