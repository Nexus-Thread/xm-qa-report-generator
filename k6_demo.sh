#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

SERVICE="megatron"
REPORT_PATH="k6_example/megatron/"

uv run qa-report-generator-k6 extract \
  --service "$SERVICE" \
  --report "$REPORT_PATH"

echo "Printed consolidated extracted_runs model for service: $SERVICE"
