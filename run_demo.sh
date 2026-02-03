#!/bin/bash
set -e

# Orchestration script for running pytest and generating reports with multiple LLM models
# This script demonstrates the reporting POC by:
# 1. Running tests in dummy_project to generate a pytest JSON report
# 2. Generating reports using different Ollama models

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        LLM-Powered Test Reporting - Demo Orchestration        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Define models to test
MODELS=(
    "llama3.2:1b-instruct-q5_K_M"
    "qwen2.5:14b-instruct-q4_K_M"
    "gpt-oss:latest"
    "gpt-oss:120b"
)

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track successful and failed models
declare -a SUCCESSFUL_MODELS
declare -a FAILED_MODELS

# Step 1: Run pytest in dummy_project
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}[1/2] Running pytest in dummy_project...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd dummy_project

# Run pytest (allow test failures, we just need the report)
pytest || true

echo ""
echo -e "${GREEN}✓ Pytest completed${NC}"
echo -e "  Report generated: ${YELLOW}dummy_project/pytest-report.json${NC}"

# Check if report was actually generated
if [ ! -f "pytest-report.json" ]; then
    echo ""
    echo -e "${RED}✗ Pytest report file not found${NC}"
    echo "  Exiting..."
    exit 1
fi

cd ..
echo ""

# Step 2: Generate reports for each model
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}[2/2] Generating reports with multiple models...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL_MODELS=${#MODELS[@]}
CURRENT=0

for MODEL in "${MODELS[@]}"; do
    CURRENT=$((CURRENT + 1))

    # Clean model name for directory (replace : with -)
    MODEL_DIR=$(echo "$MODEL" | sed 's/:/-/g')
    OUTPUT_DIR="out/$MODEL_DIR"

    echo "┌────────────────────────────────────────────────────────────────┐"
    echo -e "│ Model ${CURRENT}/${TOTAL_MODELS}: ${YELLOW}${MODEL}${NC}"
    echo "└────────────────────────────────────────────────────────────────┘"
    echo ""

    # Record start time
    START_TIME=$(date +%s)

    # Set the model in environment and run report generation
    export OPENAI_MODEL="$MODEL"

    if python -m qa_report_generator generate \
        --json-report dummy_project/pytest-report.json \
        --out "$OUTPUT_DIR" \
        --env staging \
        --build "demo-$(date +%Y%m%d-%H%M%S)" \
        --commit "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"; then

        # Calculate duration
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))

        echo ""
        echo -e "${GREEN}✓ Reports generated successfully for ${MODEL}${NC}"
        echo -e "  Output directory: ${YELLOW}${OUTPUT_DIR}/${NC}"
        echo -e "  Duration: ${DURATION}s"

        SUCCESSFUL_MODELS+=("$MODEL")
    else
        # Calculate duration
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))

        echo ""
        echo -e "${RED}✗ Report generation failed for ${MODEL}${NC}"
        echo -e "  Duration: ${DURATION}s"
        echo -e "  ${YELLOW}Continuing with next model...${NC}"

        FAILED_MODELS+=("$MODEL")
    fi

    echo ""
done

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                         SUMMARY                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${GREEN}Successful models (${#SUCCESSFUL_MODELS[@]}/${TOTAL_MODELS}):${NC}"
if [ ${#SUCCESSFUL_MODELS[@]} -eq 0 ]; then
    echo "  None"
else
    for MODEL in "${SUCCESSFUL_MODELS[@]}"; do
        MODEL_DIR=$(echo "$MODEL" | sed 's/:/-/g')
        echo -e "  ✓ ${MODEL} → out/${MODEL_DIR}/"
    done
fi

echo ""

if [ ${#FAILED_MODELS[@]} -gt 0 ]; then
    echo -e "${RED}Failed models (${#FAILED_MODELS[@]}/${TOTAL_MODELS}):${NC}"
    for MODEL in "${FAILED_MODELS[@]}"; do
        echo -e "  ✗ ${MODEL}"
    done
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Generated reports can be found in:${NC} ${YELLOW}out/${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# View reports
echo -e "${BLUE}To view reports:${NC}"
for MODEL in "${SUCCESSFUL_MODELS[@]}"; do
    MODEL_DIR=$(echo "$MODEL" | sed 's/:/-/g')
    echo "  open out/${MODEL_DIR}/test_summary.md"
    echo "  open out/${MODEL_DIR}/qa_signoff.md"
done
echo ""

# Exit with error if any models failed
if [ ${#FAILED_MODELS[@]} -gt 0 ]; then
    exit 1
fi

exit 0
