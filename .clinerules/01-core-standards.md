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
- Raise **layer-appropriate exceptions** (not generic `Exception`):
  - In `domain/` and `application/`: use domain/application-specific exceptions (typically from `domain/exceptions.py` or application exception modules).
  - In adapters: use adapter/infrastructure-specific exceptions internally when needed, then translate at adapter boundaries.
- **Never** use bare `except:`; catch the most specific exception possible.
- Preserve context with `raise CustomError(...) from err`.
- Validate inputs at module boundaries (e.g., adapters) and fail fast with clear errors.
- Avoid returning `None` for error states; raise unless the API explicitly allows it.
- Translate exceptions at the **adapter boundary** into the caller's domain (CLI/HTTP response) without leaking internal types.

## Logging
- Use the configured logger (typically from a dedicated `logging_config.py` module) — **no `print()`** in production code.
- Never log secrets, tokens, API keys, or sensitive data unless required for debugging.
- Keep logging setup centralized; do not duplicate global logging configuration in feature modules.
- For logger naming, structured context, exception logging patterns, and allowed exceptions, see `11-logging-conventions.md`.
