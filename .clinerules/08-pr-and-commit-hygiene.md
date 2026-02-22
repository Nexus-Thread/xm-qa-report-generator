# PR size limits, commit message style, review checklist, CI expectations

Use these rules to keep reviews fast, changesets focused, and CI reliable.

## PR size limits
- **Should** keep PRs under ~400 changed lines when possible.
- **Must** split large refactors into sequenced PRs unless explicitly approved.
- **Should** include a concise summary and test evidence in the PR description.

## Commit message style
- **Must** use imperative, present tense (e.g., "Add user repository adapter").
- **Should** include a scope prefix when useful (e.g., `docs:`, `tests:`, `adapters:`).
- **Must** keep commits focused; avoid mixing unrelated changes.

## Review checklist
- **Must** verify boundary compliance (ports/adapters separation).
- **Must** ensure tests updated for behavior changes.
- **Should** confirm docs updated when configuration/usage changes.
- **Should** check for logging/observability coverage on new I/O paths.

## CI expectations
- **Must** run the local quality gate before handoff (see `09-tooling-and-ci.md`).
- **Must** fix CI failures at the root cause; do not bypass checks.
