# Universal coding standards: naming, formatting, error handling, logging

Use these rules for all Python code in this repo to keep behavior predictable and reviews lightweight.

## Naming
- **Modules/files**: `snake_case.py` (e.g., `prompt_loader.py`).
- **Packages**: lowercase, no hyphens.
- **Classes**: `PascalCase` nouns (e.g., `ReportBuilder`).
- **Functions/methods**: `snake_case` verbs (e.g., `load_prompt`).
- **Constants**: `UPPER_SNAKE_CASE`.
- **Tests**: `test_<behavior>()` focused on the behavior under test.

## Formatting
- Use `ruff format .`; **do not** hand-format or fight the formatter.
- Let `ruff check . --fix` handle import ordering.
- Prefer explicit, readable code over clever one-liners.

## Boundary behavior (adapter input validation)
- Validate and normalize external inputs at **adapter boundaries** before calling application ports.
- Keep **mapping** between external schemas and DTOs/domain objects inside adapters.
- For broader hexagonal boundary doctrine, see `02-architecture-guardrails.md`.

## Error handling
- Raise **domain-specific exceptions** (see `src/qa_report_generator/domain/exceptions.py`), not generic `Exception`.
- **Never** use bare `except:`; catch the most specific exception possible.
- Preserve context with `raise CustomError(...) from err`.
- Validate inputs at module boundaries (e.g., adapters) and fail fast with clear errors.
- Avoid returning `None` for error states; raise unless the API explicitly allows it.
- Translate exceptions at the **adapter boundary** into the caller’s domain (CLI/HTTP response) without leaking internal types.

## Logging
- Use the configured logger (see `src/qa_report_generator/logging_config.py`) — **no `print()`** in production code.
- Levels:
  - `debug`: noisy diagnostics
  - `info`: flow milestones
  - `warning`: recoverable issues
  - `error`: operation failures
- Include structured context when possible via `extra={...}`.
- Use `logger.exception(...)` inside `except` blocks to capture stack traces automatically.
- Use `logger.error(...)` when no active exception is being handled.
- Never log secrets, tokens, or raw LLM prompts/responses unless required.
- Log boundary crossings at `info` with structured context (request IDs, adapter name).
