# QA Report Generator

This project uses `uv` for environment and command execution.

## Docker

Build the CLI image:

```bash
docker build -t qa-report-generator .
```

The image uses `qa-report-generator-performance` as its default entrypoint, so you can pass
CLI arguments directly after the image name.

Example with a mounted k6 report directory:

```bash
docker run --rm \
  -e LLM_API_KEY=your-api-key \
  -v "$PWD/k6_example:/data/k6_example:ro" \
  qa-report-generator \
  generate \
  --service megatron \
  --report /data/k6_example/20260228/megatron
```

Optional logging/debug environment variables such as `LOG_LEVEL`, `LOG_FORMAT`,
`LLM_MAX_CONCURRENCY`, `LLM_DEBUG_JSON_ENABLED`, and `LLM_DEBUG_JSON_DIR` can be provided the
same way with additional `-e` flags.

## Shared adapters

Reusable LLM adapter infrastructure lives in `src/shared/adapters/output/llm/`.

- OpenAI transport and response helpers are shared there.
- Structured JSON LLM completion logic is shared there.
- Application packages keep only thin boundary adapters that translate shared failures into
  application-specific exceptions.

Reusable JSON payload persistence also lives in `src/shared/adapters/output/persistence/`.

- `JsonFileWriterAdapter` provides generic timestamped JSON file persistence for debug payloads and
  other machine-readable snapshots.

## k6 CLI

### Logging configuration

The CLI uses centralized logging configured from environment-backed settings.

Environment variables:
- `LOG_LEVEL` (default: `INFO`)
- `LOG_FORMAT` (`simple` or `json`, default: `simple`)

Examples:

```bash
LOG_LEVEL=DEBUG uv run qa-report-generator-performance generate \
  --service megatron \
  --report k6_example/20260228/megatron
```

```bash
LOG_FORMAT=json uv run qa-report-generator-performance generate \
  --service megatron \
  --report k6_example/20260228/megatron
```

Notes:
- `simple` format is human-readable and suited to local CLI usage.
- `json` format emits structured logs with stable fields such as timestamp, level, logger, message, and any supported `extra` context.
- Regular logs intentionally avoid emitting raw LLM prompt/response payload content.
- If you need full request/response payload inspection, use the debug JSON artifact options below instead of relying on normal logs.

### Manual parser coverage check for fixture bundle

```bash
uv run python scripts/parse_k6_example_20260228.py
```

Optional custom input directory:

```bash
uv run python scripts/parse_k6_example_20260228.py --base-dir k6_example/20260228
```

The script parses each `*.json` file per service folder and prints per-service status,
scenario counts/names, file-level failures, and final totals.

### Generate deterministic service metrics

```bash
uv run qa-report-generator-performance generate \
  --service megatron \
  --report k6_example/20260228/megatron
```

Another built-in example:

```bash
uv run qa-report-generator-performance generate \
  --service trading \
  --report k6_example/20260228/trading
```

`qa-report-generator-performance` is the packaged CLI entry point defined in `pyproject.toml`.

Notes:
- Reports are parsed first into a normalized scenario model.
- If a service definition exists, extraction is service-scoped and schema-driven.
- If a service definition does not exist, CLI returns generic parsed scenario output.
- `LLM_API_KEY` must be provided in the environment.
- Verification is strict-fail: any numeric mismatch fails the run.
- Successful CLI runs do not emit a summary payload to stdout; operational details are emitted through logs.
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
uv run qa-report-generator-performance generate \
  --service megatron \
  --report k6_example/20260228/megatron
```

Environment variables:
- `LLM_API_KEY` (required)
- `LLM_MAX_CONCURRENCY` (default: `4`)
- `LLM_INPUT_COST_PER_MILLION_TOKENS` (optional)
- `LLM_OUTPUT_COST_PER_MILLION_TOKENS` (optional)
- `LLM_DEBUG_JSON_ENABLED` (default: `false`)
- `LLM_DEBUG_JSON_DIR` (default: `out/debug/llm`)

When multiple parsed scenarios are present, service-specific extraction can process them in parallel
using a synchronous worker pool. `LLM_MAX_CONCURRENCY` bounds how many scenarios may issue
overlapping OpenAI-compatible requests at once while preserving deterministic output order.

Normal logs include metadata about structured LLM stages, retry behavior, and LLM usage/cost summaries,
while the optional debug JSON files contain the raw request/response/parsed payload artifacts for deeper inspection.

When pricing variables are configured, the CLI emits one aggregated LLM cost log event per run.
If token usage is returned but pricing is not configured, the log still includes token counts with
`estimated_cost_usd=null`.

## Adding a new service extraction module

1. Create a new package under:
   - `src/qa_report_generator_performance/application/service_definitions/services/<service_name>/`
2. Implement:
   - `schema.py`: Pydantic model(s)
   - `prompts.py`: extraction + verification prompt builders
   - optional schema/model validators for service-specific invariants
   - `definition.py`: `ServiceDefinition` instance
   - `__init__.py`: export `SERVICE_DEFINITION`
3. No central registry edit is required for in-repo definitions:
   - built-in definitions are discovered automatically from `service_definitions/services/*` packages.
   - current built-in examples include `megatron`, `trading`, `symbolsservice`, `symbolstreeservice`, `tradinghistoricaldata`, `vps`, and `watchlists`.
4. Keep extraction deterministic:
   - preserve exact numeric values,
   - keep canonical JSON serialization in prompts,
   - include mismatch JSONPath fields in verification response.
