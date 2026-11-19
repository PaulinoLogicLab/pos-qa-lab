#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export RUN_DEVICE_TESTS=1
python scripts/run_suite.py --device --no-api "$@"
