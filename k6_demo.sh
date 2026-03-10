#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPORT_ROOT="k6_example/20260228"

cd "$SCRIPT_DIR"

for SERVICE in \
  megatron \
  symbolsservice \
  symbolstreeservice \
  trading \
  tradinghistoricaldata \
  vps \
  watchlists
do
  REPORT_PATH="${REPORT_ROOT}/${SERVICE}/"
  uv run qa-report-generator-k6 generate \
    --service "$SERVICE" \
    --report "$REPORT_PATH"
done
