# Hexagonal architecture doctrine (hard constraints)

Use this doctrine as the default architecture standard for this repo. Any deviation must be explicitly documented.

## Core principles (non-negotiable)
- **Dependency direction**: All dependencies point **inward** toward the domain and application core.
- **Business logic isolation**: Domain models are pure and independent of frameworks, I/O, and infrastructure.
- **Explicit boundaries**: Interaction between layers happens only through ports (interfaces/protocols).
- **Replaceable adapters**: I/O details are swappable without changing the core.

## Vocabulary
- **Domain**: Entities, value objects, domain services, and domain errors. No I/O concerns.
- **Application**: Use cases orchestration. Defines **ports** (input/output) and coordinates domain behavior.
- **Ports**: Contracts that isolate the core from infrastructure. Input ports (commands/queries) and output ports (persistence, messaging, external APIs).
- **Adapters**: Implementation of ports at the system edge (CLI, HTTP, DB, LLM, queues, etc.).
- **Infrastructure**: Frameworks, SDKs, DB drivers, HTTP clients, serializers, etc. Lives only in adapters.

## Dependency rules (allowed/forbidden)
✅ **Allowed**
- Domain → Domain (same layer)
- Application → Domain
- Adapters → Application ports + Domain (through ports or DTOs)

❌ **Forbidden**
- Domain → Application, Adapters, Infrastructure
- Application → Adapters, Infrastructure
- Adapter → Adapter (unless through application ports)

## Layer responsibilities
### Domain
- Pure business rules and invariants.
- No side effects, no I/O, no framework imports.
- Exposes domain errors and value objects.

### Application (Use Cases)
- Orchestrates flows, validates inputs (structural validation), invokes domain logic.
- Defines ports and DTOs that are **inward-facing** and stable.
- Handles cross-cutting concerns like transactions or unit-of-work abstractions.

### Ports
- **Input ports**: Methods used by driving adapters (CLI/HTTP/Jobs).
- **Output ports**: Interfaces for persistence, external services, or notifications.
- Ports are defined in the application layer only.

### Adapters
- Implement ports for external systems.
- Translate external data structures ↔ DTOs/domain objects.
- Handle I/O, serialization, transport, retry logic.

## Module/package structure guidance
- `domain/`: entities, value objects, domain services, domain errors.
- `application/`: use cases + ports + DTOs.
- `adapters/`: input (CLI/HTTP) and output (persistence, APIs, LLM, etc.).
- `infrastructure/` (optional): shared infra utilities used by adapters only.

## Naming conventions (layer-aware)
- `.../ports/` for interfaces/protocols.
- `.../adapters/input/` and `.../adapters/output/` for adapter implementations.
- DTOs named for their intent: `CreateReportCommand`, `ReportSummaryDTO`.

## No-go examples (explicitly banned)
- Importing an HTTP client in `domain/` or `application/`.
- ORM models inside domain entities.
- Adapters calling each other directly instead of via application ports.
- "Helper" utilities in `domain/` that perform I/O.

## Adapter directory structure
Adapters at the same conceptual level **must** be organized uniformly to keep navigation predictable and scalable.

### Directory structure rules
- **Must** organize adapters in subdirectories (not as standalone files) when multiple adapters exist in the same parent directory.
- **Should** use subdirectories even for simple, single-file adapters to maintain consistency and allow future expansion without restructuring.
- **Must** name the main implementation file semantically: `adapter.py`, `parser.py`, `writer.py`, `client.py`, etc. (never repeat the directory name).
- **Must** export public classes from the subdirectory's `__init__.py` to keep imports clean.

### Pattern: output adapters
When you have multiple output adapters (e.g., persistence, narrative, parsers), each should follow the same structure:

✅ **Consistent structure**
```
adapters/output/
├── persistence/
│   ├── cache/
│   │   ├── __init__.py       # Exports FileReportCache
│   │   └── adapter.py        # Implementation
│   └── markdown_writer/
│       ├── __init__.py       # Exports MarkdownReportWriter
│       ├── adapter.py        # Main class
│       ├── formatters.py
│       └── renderers.py
├── narrative/
│   ├── __init__.py
│   └── llm_adapter.py
└── parsers/
    ├── __init__.py
    └── pytest_json_parser.py
```

❌ **Inconsistent structure (avoid)**
```
adapters/output/
├── persistence/
│   ├── cache.py               # ❌ Standalone file
│   └── markdown_writer/       # ✅ Subdirectory
│       └── ...
```

### Naming conventions
- Directory: `snake_case` (e.g., `report_cache/`, `llm_client/`, `markdown_writer/`)
- Main file: semantic name matching responsibility (e.g., `adapter.py`, `parser.py`, `writer.py`)
- Supporting files: `types.py`, `formatters.py`, `validators.py`, `serializers.py`, etc.

### Exceptions
- When there's only **one** adapter in a category and no plans for more, a single file may be acceptable.
- Document the reasoning if deviating from the standard structure.
