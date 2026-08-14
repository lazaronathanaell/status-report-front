#!/usr/bin/env sh
set -eu
BENCH_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python3 "$BENCH_DIR/matrix_runner.py" --matrix "${1:-matrix.json}" --env-file "${2:-configs/example.env}"
