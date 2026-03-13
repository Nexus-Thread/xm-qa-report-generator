#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
REPORT_ROOT="${REPO_ROOT}/k6_example/20260228"

cd "$REPO_ROOT"

for SERVICE in \
  megatron \
  symbolsservice \
  symbolstreeservice \
  trading \
  tradinghistoricaldata \
  vps \
  watchlists
do
  REPORT_PATH="${REPORT_ROOT}/${SERVICE}"
  uv run qa-report-generator-performance generate \
    --service "$SERVICE" \
    --report "$REPORT_PATH"
done
