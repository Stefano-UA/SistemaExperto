#!/bin/bash
# Script to run unit tests and generate a coverage report

HERE="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"

source "${HERE}/init.sh"

cd "${HERE}/.." || exit 1

pytest --cov=src test/