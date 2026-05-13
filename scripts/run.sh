#!/bin/bash
# Script to launch the Fuzzy Expert System application

HERE="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

source "${HERE}/init.sh"

export PYTHONPATH="${HERE}/../src:${PYTHONPATH}"
echo "Starting the application..."
python "${HERE}/../src/main.py"