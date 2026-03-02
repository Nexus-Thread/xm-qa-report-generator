# QA Report Generator

## k6 CLI

### Generate consolidated summary rows (printed JSON)

```bash
qa-report-generator-k6 generate \
  --report k6_example/megatron
```

### Extract deterministic service metrics (phase 1)

```bash
qa-report-generator-k6 extract \
  --service megatron \
  --report k6_example/megatron/megatron-1.json
```

Notes:
- Extraction is service-scoped and schema-driven.
- Verification is strict-fail: any numeric mismatch fails the run.
- Output is printed to the console as parsed JSON models.

## Adding a new service extraction module

1. Create a new package under:
   - `src/qa_report_generator/application/service_definitions/<service_name>/`
2. Implement:
   - `schema.py`: Pydantic model(s)
   - `prompts.py`: extraction + verification prompt builders
   - `validation.py`: service-specific invariants
   - `definition.py`: `ServiceDefinition` instance
   - `__init__.py`: export `SERVICE_DEFINITION`
3. No central registry edit is required for in-repo definitions:
   - built-in definitions are discovered automatically from `service_definitions/*` packages.
4. Optional plugin path for external service packs:
   - set `PLUGIN_MODULES` (comma-separated) in env,
   - plugin module imports and calls `register_service_definition(...)`.
5. Keep extraction deterministic:
   - preserve exact numeric values,
   - keep canonical JSON serialization in prompts,
   - include mismatch JSONPath fields in verification response.
