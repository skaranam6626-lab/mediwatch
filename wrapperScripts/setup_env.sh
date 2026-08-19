#!/bin/bash
# Shared Python environment setup for mediwatch wrapper scripts.

setup_python_env() {
    local req_file="${1:-requirements.txt}"

    # Inside Docker/Airflow: use the container interpreter; do not create a venv.
    if [ -f /.dockerenv ] || [ -n "${AIRFLOW_HOME:-}" ]; then
        echo "Using container Python (skipping venv)..."
        export PATH="${HOME}/.local/bin:${PATH}"
        return 0
    fi

    # Local dev: recreate the venv if it is missing or incomplete.
    if [ ! -x .venv/bin/python ]; then
        echo "Creating virtual environment..."
        rm -rf .venv
        python3 -m venv .venv
    fi

    # shellcheck source=/dev/null
    source .venv/bin/activate
    export PIP_USER=false
    pip install --upgrade pip
    pip install -r "$req_file"
}
