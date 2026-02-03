# ADR 0001: Adopt Hexagonal Architecture

## Context

The reporting PoC needs a clean separation between business logic and I/O concerns. We integrate with
external systems (CLI, filesystem, LLM providers) and expect future extension points (plugins). Without
clear boundaries, adapters can leak into the core and make the domain harder to test and evolve.

## Decision

Adopt **hexagonal architecture** with strict dependency direction:

- **Domain**: pure business rules and invariants, no I/O
- **Application**: use cases + ports; orchestrates domain logic
- **Adapters**: input/output implementations for CLI, parsing, persistence, LLM

All dependencies point inward. Adapters depend on application ports and domain models; the core does not
depend on adapters or infrastructure frameworks.

## Consequences

- Clear layering and testability across domain/application layers
- Adapters remain replaceable and easier to mock for tests
- Requires explicit ports and wiring in the composition root
- Additional discipline is needed to prevent boundary violations

## Alternatives

- **Layered architecture** (package-by-feature) without strict ports: simpler but less explicit boundaries
- **Monolith with shared helpers**: faster short-term but creates long-term coupling and test pain
