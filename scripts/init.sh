#!/bin/bash
# Script for initializing the execution environment

HERE="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

if [ ! -f "${HERE}/../.env" ]; then
    echo "Copying .env.example to .env..."
    cp "${HERE}/../.env.example" "${HERE}/../.env"
fi

# Source .env and export variables automatically
set -a; source "${HERE}/../.env"; set +a

if [ ! -d "${HERE}/../.venv" ]; then
    echo "Creating virtual environment..."
    python -m venv "${HERE}/../.venv"
    source "${HERE}/../.venv/bin/activate"
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source "${HERE}/../.venv/bin/activate"
fi
