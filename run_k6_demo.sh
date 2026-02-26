#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python -m qa_report_generator.cli_k6 k6-summary \
  --reports-dir k6_example/reports \
  --out-file k6_example/generated/performance_summary.md

echo "k6 summary generated at: k6_example/generated/performance_summary.md"
