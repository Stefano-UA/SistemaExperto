#!/bin/bash
# Script to launch the Fuzzy Expert System application

HERE="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

source "${HERE}/init.sh"

cd "${HERE}/../src" || exit 1
echo "Starting the application..."
python main.py