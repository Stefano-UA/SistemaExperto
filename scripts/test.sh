#!/bin/bash
# Simple script to run all tests using pytest

HERE="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

source "${HERE}/init.sh"

cd "${HERE}/.." || exit 1
echo "Running unit tests with pytest..."
pytest test/