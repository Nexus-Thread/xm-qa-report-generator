#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

SERVICE="megatron"
REPORT_PATH="k6_example/20260228/megatron/"
export LLM_DEBUG_JSON_ENABLED=true
uv run qa-report-generator-k6 generate \
  --service "$SERVICE" \
  --report "$REPORT_PATH"


SERVICE="symbolsservice"
REPORT_PATH="k6_example/20260228/symbolsservice/"
export LLM_DEBUG_JSON_ENABLED=true
uv run qa-report-generator-k6 generate \
  --service "$SERVICE" \
  --report "$REPORT_PATH"


SERVICE="symbolstreeservice"
REPORT_PATH="k6_example/20260228/symbolstreeservice/"
export LLM_DEBUG_JSON_ENABLED=true
uv run qa-report-generator-k6 generate \
  --service "$SERVICE" \
  --report "$REPORT_PATH"


SERVICE="trading"
REPORT_PATH="k6_example/20260228/trading/"
export LLM_DEBUG_JSON_ENABLED=true
uv run qa-report-generator-k6 generate \
  --service "$SERVICE" \
  --report "$REPORT_PATH"


SERVICE="tradinghistoricaldata"
REPORT_PATH="k6_example/20260228/tradinghistoricaldata/"
export LLM_DEBUG_JSON_ENABLED=true
uv run qa-report-generator-k6 generate \
  --service "$SERVICE" \
  --report "$REPORT_PATH"


SERVICE="vps"
REPORT_PATH="k6_example/20260228/vps/"
export LLM_DEBUG_JSON_ENABLED=true
uv run qa-report-generator-k6 generate \
  --service "$SERVICE" \
  --report "$REPORT_PATH"


SERVICE="watchlists"
REPORT_PATH="k6_example/20260228/watchlists/"
export LLM_DEBUG_JSON_ENABLED=true
uv run qa-report-generator-k6 generate \
  --service "$SERVICE" \
  --report "$REPORT_PATH"
