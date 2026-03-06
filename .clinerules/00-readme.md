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

## Rule authoring standards
- Keep each module focused on one primary topic with a clearly implied owner.
- Avoid restating requirements owned by another module unless the later module is adding stricter or more specific constraints.
- Prefer one requirement per bullet so review discussions can reference a single rule precisely.
- Use **Must** only for review-blocking requirements.
- Use **Should** for strong defaults that may allow justified exceptions.
- When a later module intentionally overrides or sharpens an earlier rule, make that override explicit.

## Ownership and specialization
- Earlier files should define broad policy and defaults for their topic.
- Later specialized files should define detailed mechanics for narrower subtopics.
- When a specialized file exists, earlier files should point to it instead of repeating detailed guidance.

### Topic ownership map
- `01-core-standards.md`: universal coding behavior and defaults
- `02-architecture-guardrails.md`: architecture boundaries and dependency direction
- `03-testing-standards.md`: automated testing expectations
- `04-docs-and-adr.md`: required project documentation outside source code
- `05-module-structure.md`: file, package, and export mechanics
- `06-performance-and-observability.md`: performance expectations and runtime visibility
- `07-repo-navigation.md`: repository discovery and navigation guidance
- `08-pr-and-commit-hygiene.md`: review and change-management discipline
- `09-tooling-and-ci.md`: local quality gate and CI workflow expectations
- `10-documentation-standards.md`: in-code documentation style only
- `11-logging-conventions.md`: logging implementation mechanics only
- `12-command-execution-safety.md`: command execution and process safety

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

Interpret enforcement labels as follows:
- **Tool-enforced**: verified directly by automated tooling.
- **Review-enforced**: verified primarily in code review.
- **Process-enforced**: verified through operating discipline when tools cannot reliably enforce the rule.

| Rule area | Primary enforcement | Secondary enforcement |
| --- | --- | --- |
| Naming, formatting, imports | `ruff format .`, `ruff check . --fix`, `ruff check .` | PR review |
| Type contracts and API drift | `mypy src/ tests/` | PR review |
| Behavior changes and regressions | `pytest tests/` | Targeted regression tests |
| Architecture boundaries (hexagonal) | Review-enforced against `02-architecture-guardrails.md` | Optional import-lint/custom boundary scripts |
| Module/file structure conventions | Review-enforced against `05-module-structure.md` | Optional repository audit script |
| Docs/ADR/changelog updates | Review-enforced via PR checklist | Release checklist |
| Logging conventions | Review-enforced against `11-logging-conventions.md` | Runtime log sampling |
| Command execution safety | Process-enforced (no `python - <<'PY'` patterns; git `--no-pager`/non-interactive) | PR review |

## Rules-to-enforcement alignment
- Hard constraints should be backed by tool enforcement where practical; otherwise, mark them as review-enforced or process-enforced.
- If automation cannot fully enforce a rule, write the rule so a reviewer can still evaluate compliance consistently.
- Keep rule text, examples, and tooling configuration aligned; when they differ intentionally, document the reason in the relevant rule file or PR notes.

## Scope
These rules apply to Python projects using hexagonal architecture unless explicitly stated otherwise.

## Project-specific customization
For project-specific navigation and structure details:
1. Use the workflow in `workflows/update-repo-navigation.md` to generate a current map
2. Store project-specific documentation in `docs/` or the project root
3. Keep `.clinerules/` generic and portable across projects
