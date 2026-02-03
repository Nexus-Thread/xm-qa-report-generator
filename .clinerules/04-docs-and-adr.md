# Docs rules: README updates, ADR format, changelog notes, API docs

Use these rules to keep documentation consistent and decision records traceable.

## README updates
- **Must** update `README.md` when behavior, configuration, or usage changes.
- **Should** add short usage examples when new CLI flags or commands are introduced.
- **Must** document new environment variables and defaults.

## ADR (Architecture Decision Records)
- **Must** create an ADR when a decision impacts architecture, dependencies, or boundaries.
- **Must** use the format: **Context**, **Decision**, **Consequences**, **Alternatives**.
- **Should** include links to related issues/PRs.

## Changelog notes
- **Must** call out breaking changes explicitly.

## API docs rules
- **Should** document public ports, CLI interfaces, and plugin extension points.
- **Must** keep DTO field meanings aligned with domain terminology.
