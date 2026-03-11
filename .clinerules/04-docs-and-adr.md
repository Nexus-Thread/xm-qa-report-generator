# Docs rules: README updates, ADR format, changelog notes, API docs

Use these rules to keep documentation consistent and decision records traceable.

## README updates
- **Must** update `README.md` when behavior, configuration, or usage changes.
- **Should** add short usage examples when new CLI flags or commands are introduced.
- **Must** document new environment variables and defaults.
- **Should** document supported Python version(s), the `uv` workflow (`uv sync`, `uv run ...`), and the local quality gate commands when they are project-relevant.
- In-code docstring and comment style is governed separately by `10-documentation-standards.md`.

## ADR (Architecture Decision Records)
- **Must** create an ADR when a decision impacts architecture, dependencies, or boundaries.
- **Must** include at minimum: **Context**, **Decision**, **Consequences**, **Alternatives**.
- **Should** also record ADR metadata such as **Status**, **Date**, and supersedes/replaces links when applicable.
- **Should** include links to related issues/PRs.
- Put architectural rationale in ADRs rather than module docstrings or inline comments.

## Changelog notes
- **Must** call out breaking changes explicitly.
- **Must** record release-facing changes in `CHANGELOG.md` when that file exists.
- **Should** include a concise changelog-style summary in PR notes when `CHANGELOG.md` is not maintained.

## API docs rules
- **Should** document public ports, CLI interfaces, and plugin extension points.
- **Must** keep DTO field meanings aligned with domain terminology.
- **Should** document caller-visible error semantics, idempotency/retry expectations, and pagination/streaming behavior for external interfaces when relevant.
