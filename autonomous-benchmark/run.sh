#!/usr/bin/env sh
set -eu

BENCH_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE=${1:-"$BENCH_DIR/configs/22001149961202519.env"}
COMPOSE="docker compose -f $BENCH_DIR/compose.yml --env-file $ENV_FILE"

$COMPOSE up -d --build --wait ollama
$COMPOSE run --rm model-pull
$COMPOSE up -d --build metrics
status=0
$COMPOSE up --build --no-deps benchmark || status=$?
$COMPOSE wait metrics
$COMPOSE down
exit "$status"
