#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

OUTPUT_PATH="out/k6/performance_summary.md"

uv run qa-report-generator-k6 generate \
  --report k6_example/megatron \
  --out-file "$OUTPUT_PATH"

echo "Generated merged k6 summary: $OUTPUT_PATH"
