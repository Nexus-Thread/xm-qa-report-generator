# Hexagonal architecture doctrine (hard constraints)

Use this doctrine as the default architecture standard for the codebase. Any deviation must be explicitly documented.

## Core principles (non-negotiable)
- **Dependency direction**: All dependencies point **inward** toward the domain and application core.
- **Business logic isolation**: Domain models are pure and independent of frameworks, I/O, and infrastructure.
- **Explicit boundaries**: Interaction between layers happens only through ports (interfaces/protocols).
- **Replaceable adapters**: I/O details are swappable without changing the core.

## Vocabulary
- **Domain**: Entities, value objects, domain services, and domain errors. No I/O concerns.
- **Application**: Use cases orchestration. Defines **ports** (input/output) and coordinates domain behavior.
- **Ports**: Contracts that isolate the core from infrastructure. Input ports (commands/queries) and output ports (persistence, messaging, external APIs).
- **Adapters**: Implementation of ports at the system edge (CLI, HTTP, DB, external APIs, message queues, etc.).
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
- Value objects should be immutable, or treated as immutable by convention, when mutation would weaken invariants.

### Application (Use Cases)
- Orchestrates flows, validates inputs (structural validation), invokes domain logic.
- Keeps business invariants in the domain; application-level validation should focus on command shape, authorization, orchestration, and transaction boundaries.
- Defines ports and DTOs that are **inward-facing** and stable.
- Handles cross-cutting concerns like transactions or unit-of-work abstractions.

### Ports
- **Input ports**: Methods used by driving adapters (CLI/HTTP/Jobs).
- **Output ports**: Interfaces for persistence, external services, or notifications.
- Ports are defined in the application layer only.
- Prefer small, explicit port contracts expressed via `Protocol` or ABCs.
- Port signatures must use domain/application types rather than transport schemas, ORM models, or framework request/response objects.

### Adapters
- Implement ports for external systems.
- Translate external data structures ↔ DTOs/domain objects.
- Handle I/O, serialization, transport, retry logic.

## Composition root and framework isolation
- **Must** keep dependency wiring, service construction, and framework bootstrapping in entry points or dedicated bootstrap/composition-root modules.
- **Must** keep framework request/response objects, ORM models, serializer models, and transport schemas inside adapters.
- **Must** keep environment/config lookups, secret loading, and framework settings access in adapters or bootstrap modules rather than scattering them through the core.
- **Should** keep transport/event-loop concerns at I/O boundaries; use async in the core only when business semantics truly require asynchronous contracts.
- **Must not** let dependency-injection containers or service locators leak into domain entities or application use cases.

## Transactions and side effects
- **Must** coordinate transactions, unit-of-work boundaries, and side-effect ordering in the application layer or adapter-owned infrastructure boundaries.
- **Must not** hide persistence commits, network retries, or message publication inside domain entities.
- Domain events may be modeled in the core, but publication and delivery mechanics belong behind output ports/adapters.

## Module/package structure guidance
- `domain/`: entities, value objects, domain services, domain errors.
- `application/`: use cases + ports + DTOs.
- `adapters/`: input (CLI/HTTP/GraphQL) and output (persistence, external APIs, messaging, etc.).
- `infrastructure/` (optional): shared infra utilities used by adapters only.
- Detailed file splitting, package export, and `__init__.py` mechanics are governed by `05-module-structure.md`.

## Naming conventions (layer-aware)
- `.../ports/` for interfaces/protocols.
- `.../adapters/input/` and `.../adapters/output/` for adapter implementations.
- DTOs named for their intent: `CreateOrderCommand`, `UserProfileDTO`, `PaymentResultDTO`.

## No-go examples (explicitly banned)
- Importing an HTTP client in `domain/` or `application/`.
- ORM models inside domain entities.
- Adapters calling each other directly instead of via application ports.
- "Helper" utilities in `domain/` that perform I/O.

## Adapter directory structure
Adapters at the same conceptual level **must** be organized uniformly to keep navigation predictable and scalable.

- **Must** keep adapter structure consistent within the same conceptual category.
- **Must** avoid mixing one-off standalone adapters with subdirectory-based adapters without a documented reason.
- **Must** keep adapter naming and packaging aligned with the package-structure rules in `05-module-structure.md`.
- For detailed directory, file naming, and export conventions, follow `05-module-structure.md`.
