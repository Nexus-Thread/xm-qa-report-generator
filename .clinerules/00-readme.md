# How this ruleset is structured + how to toggle modules

## Structure and ordering
- Files in `.clinerules/` are **active** rules.
- Rule files are ordered by the numeric prefix (e.g., `01-`, `02-`) to keep a consistent reading order.
- Each file should focus on a single theme (core standards, architecture, testing, etc.).

## Rule precedence and conflict resolution
- Treat rules marked as **hard constraints** or **non-negotiable** as highest priority within `.clinerules/`.
- **Must** statements take precedence over **Should** statements.
- If two rules with the same strength conflict, the rule in the higher-numbered file wins.
- Any intentional deviation must be documented in ADR/PR notes.

## Toggling modules
- To **disable** a rule set temporarily, move the file to `.clinerules-bank/`.
- To **enable** a rule set, move it back to `.clinerules/`.
- Keep filenames identical when moving between folders so history remains clear.

## Adding or updating rules
- Prefer **small, focused** rule files rather than large monoliths.
- Use **Must/Should** language for clarity and consistency.
- When adding a new module, update this README and ensure numbering remains sequential.

## Active modules
- `01-core-standards.md` - Naming, formatting, error handling, logging
- `02-architecture-guardrails.md` - Hexagonal architecture doctrine, adapter directory structure
- `03-testing-standards.md` - Testing pyramid, pytest conventions
- `04-docs-and-adr.md` - README updates, ADR format, changelog notes
- `05-module-structure.md` - File organization, splitting rules, `__init__.py` conventions
- `06-performance-and-observability.md` - Profiling, tracing, metrics
- `07-repo-navigation.md` - Generic navigation guidelines for hexagonal architecture
- `08-pr-and-commit-hygiene.md` - PR size, commit messages, reviews
- `09-tooling-and-ci.md` - Local quality gate, CI expectations
- `10-documentation-standards.md` - Clear, concise docstrings and comments
- `11-logging-conventions.md` - Module-level logger standard and exceptions
- `12-command-execution-safety.md` - Hard ban on inline interpreter heredocs; require temp scripts and non-interactive git usage

## Workflows
- `workflows/update-repo-navigation.md` - Generate project-specific navigation maps on demand

## Enforcement and automation matrix
Use this map to keep "Must" rules enforceable, not just advisory.

| Rule area | Primary enforcement | Secondary enforcement |
| --- | --- | --- |
| Naming, formatting, imports | `ruff format .`, `ruff check . --fix`, `ruff check .` | PR review |
| Type contracts and API drift | `mypy src/ tests/` | PR review |
| Behavior changes and regressions | `pytest tests/` | Targeted regression tests |
| Architecture boundaries (hexagonal) | Code review vs `02-architecture-guardrails.md` | Optional import-lint/custom boundary scripts |
| Module/file structure conventions | Code review | Optional repository audit script |
| Docs/ADR/changelog updates | PR checklist/review | Release checklist |
| Logging conventions | `ruff` + code review | Runtime log sampling |
| Command execution safety | Process discipline (no `python - <<'PY'` patterns; git `--no-pager`/non-interactive) | PR review |

## Scope
These rules apply to Python projects using hexagonal architecture unless explicitly stated otherwise.

## Project-specific customization
For project-specific navigation and structure details:
1. Use the workflow in `workflows/update-repo-navigation.md` to generate a current map
2. Store project-specific documentation in `docs/` or the project root
3. Keep `.clinerules/` generic and portable across projects
