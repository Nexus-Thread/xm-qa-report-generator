# QA Report Generator

## k6 CLI

### Manual parser coverage check for fixture bundle

```bash
python scripts/parse_k6_example_20260228.py
```

Optional custom input directory:

```bash
python scripts/parse_k6_example_20260228.py --base-dir k6_example/20260228
```

The script parses each `*.json` file per service folder and prints per-service status,
scenario counts/names, file-level failures, and final totals.

### Generate deterministic service metrics

```bash
qa-report-generator-k6 generate \
  --service megatron \
  --report k6_example/megatron
```

Another built-in example:

```bash
qa-report-generator-k6 generate \
  --service trading \
  --report k6_example/20260228/trading
```

Notes:
- Reports are parsed first into a normalized scenario model.
- If a service definition exists, extraction is service-scoped and schema-driven.
- If a service definition does not exist, CLI returns generic parsed scenario output.
- `LLM_API_KEY` must be provided in the environment.
- Verification is strict-fail: any numeric mismatch fails the run.
- Output is printed as one consolidated summary envelope for the extracted service.
- `runs` always contains the final consumer-facing result after the pipeline finishes.
- For services without custom post-processing, `runs` contains the extracted scenarios as-is.
- For services with custom post-processing, `runs` contains the post-processed result in the same interface.
- `symbolstreeservice` currently uses this step to merge numbered `getSymbolsTreeInfo{number}` scenarios into grouped final runs.

### Optional structured LLM debug JSON dumps

You can persist low-level structured LLM payloads (request, response content, parsed JSON) into files:

```bash
LLM_API_KEY=your-api-key \
LLM_DEBUG_JSON_ENABLED=true \
LLM_DEBUG_JSON_DIR=out/debug/llm \
qa-report-generator-k6 generate \
  --service megatron \
  --report k6_example/megatron
```

Environment variables:
- `LLM_API_KEY` (required)
- `LLM_MAX_CONCURRENCY` (default: `4`)
- `LLM_DEBUG_JSON_ENABLED` (default: `false`)
- `LLM_DEBUG_JSON_DIR` (default: `out/debug/llm`)

When multiple parsed scenarios are present, service-specific extraction can process them in parallel
using a synchronous worker pool. `LLM_MAX_CONCURRENCY` bounds how many scenarios may issue
overlapping OpenAI-compatible requests at once while preserving deterministic output order.

## Adding a new service extraction module

1. Create a new package under:
   - `src/qa_report_generator/application/service_definitions/<service_name>/`
2. Implement:
   - `schema.py`: Pydantic model(s)
   - `prompts.py`: extraction + verification prompt builders
   - optional schema/model validators for service-specific invariants
   - `definition.py`: `ServiceDefinition` instance
   - `__init__.py`: export `SERVICE_DEFINITION`
3. No central registry edit is required for in-repo definitions:
   - built-in definitions are discovered automatically from `service_definitions/*` packages.
   - current built-in examples include `megatron`, `trading`, `symbolsservice`, `symbolstreeservice`, `tradinghistoricaldata`, `vps`, and `watchlists`.
4. Keep extraction deterministic:
   - preserve exact numeric values,
   - keep canonical JSON serialization in prompts,
   - include mismatch JSONPath fields in verification response.
