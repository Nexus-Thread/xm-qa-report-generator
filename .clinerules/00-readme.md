# How this ruleset is structured + how to toggle modules

## Structure and ordering
- Files in `.clinerules/` are **active** rules.
- Rule files are ordered by the numeric prefix (e.g., `01-`, `02-`) to keep a consistent reading order.
- Each file should focus on a single theme (core standards, architecture, testing, etc.).

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
- `07-repo-navigation.md` - Where things live in /src, /tests, /docs
- `08-pr-and-commit-hygiene.md` - PR size, commit messages, reviews
- `09-tooling-and-ci.md` - Local quality gate, CI expectations
- `10-documentation-standards.md` - Clear, concise docstrings and comments

## Scope
These rules apply to all work in this repository unless explicitly stated otherwise.
