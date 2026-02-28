# QA Report Generator

## k6 CLI

### Generate consolidated markdown summary

```bash
qa-report-generator-k6 generate \
  --report k6_example/megatron \
  --out-file out/k6/performance_summary.md
```

### Extract deterministic service metrics (phase 1)

```bash
qa-report-generator-k6 extract \
  --service megatron \
  --report k6_example/megatron/megatron-1.json \
  --out-file out/k6/extracted_megatron.json
```

Notes:
- Extraction is service-scoped and schema-driven.
- Verification is strict-fail: any numeric mismatch fails the run.
- Output artifact is extracted JSON only.

## Adding a new service extraction module

1. Create a new package under:
   - `src/qa_report_generator/application/service_definitions/<service_name>/`
2. Implement:
   - `schema.py`: Pydantic model(s)
   - `prompts.py`: extraction + verification prompt builders
   - `validation.py`: service-specific invariants
   - `definition.py`: `ServiceDefinition` instance
   - `__init__.py`: export `SERVICE_DEFINITION`
3. Register the new definition in:
   - `src/qa_report_generator/application/service_definitions/__init__.py`
4. Keep extraction deterministic:
   - preserve exact numeric values,
   - keep canonical JSON serialization in prompts,
   - include mismatch JSONPath fields in verification response.
