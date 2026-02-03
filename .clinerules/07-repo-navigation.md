# “Where things live”: map of /src, /tests, /docs, /infra + how to search

Use this map when deciding where new code or documentation should live.

## Source layout
- `src/qa_report_generator/domain/`: entities, value objects, domain errors.
- `src/qa_report_generator/application/`: use cases, DTOs, and ports.
- `src/qa_report_generator/adapters/input/`: CLI/HTTP adapters and request parsing.
- `src/qa_report_generator/adapters/output/`: persistence, LLM, external services.
- `src/qa_report_generator/plugins/`: plugin discovery and registries.
- `src/qa_report_generator/templates/`: prompt templates and loaders.

## Tests
- `tests/unit/`: Unit tests mirroring the `src/qa_report_generator/` structure:
  - `tests/unit/domain/`: domain model and analytics tests
  - `tests/unit/application/`: use case and strategy tests
  - `tests/unit/adapters/`: adapter tests (input/output)
  - `tests/unit/plugins/`: plugin registry tests
- `tests/int/`: adapter integration tests with real I/O or realistic fakes.
- Tests mirror the source module structure for easy navigation.

**For testing standards (pyramid, mocks, coverage), see `03-testing-standards.md`.**

## Docs and plans
- `README.md`: onboarding, usage, and configuration.
- `examples/`: runnable examples and integration snippets.

## Search tips
- Prefer `rg "<term>" src/ tests/` for fast code search.
- Use `rg "class|def" src/qa_report_generator/<area>` to explore definitions quickly.
- Look for adapter wiring in `src/qa_report_generator/cli.py` and `__main__.py`.
