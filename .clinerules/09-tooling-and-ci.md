# Tooling & CI Conventions (Python)

## Local Quality Gate (must pass before creating PR)
Run this workflow at the end of each coding session when code has been changed, and always before handoff.

When validating changes, use this order:

1. **Format + Auto-fix**
   - `ruff format .`
   - `ruff check . --fix`

2. **Lint (no auto-fixes)**
   - `ruff check .`

3. **Type check**
   - `mypy src/ tests/`

4. **Tests**
   - `pytest tests/`

## Expectations
- Generated code MUST satisfy `ruff check .` with zero violations.
- Code MUST be formatted with `ruff format .`.
- If you change behavior, you MUST add/adjust tests and run `pytest tests/`.
- Do not disable lint rules unless explicitly requested; prefer refactoring.
- CI failures must be fixed at the root cause.

## Usage clarifications
- Run the full quality gate before handoff, even if only a single file changed.
- If a change impacts only a subset of tests, run that subset first,
  but still complete the full suite before handoff.
- For flaky or slow tests, document the reason and mitigation in the handoff notes.
- If any step fails, address the underlying issue rather than proceeding to the next step.

## Architecture validation
- If a change crosses layers, include tests that prove boundary adherence (ports invoked, adapters wired).
- Document any intentional rule exceptions in the PR description and handoff notes.
