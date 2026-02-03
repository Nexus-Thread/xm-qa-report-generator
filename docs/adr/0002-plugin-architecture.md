# ADR 0002: Use a Plugin Architecture for Parsers/Writers/Hooks

## Context

The reporting PoC must support multiple input formats (parsers), output formats (writers),
and optional workflow hooks. Hard-coding these integrations would make extension expensive
and require core changes for every new integration.

## Decision

Adopt a **plugin registry** pattern for adapters:

- Parsers, writers, and hooks register via decorators or explicit module imports
- The application resolves implementations via registries
- Composition root controls plugin discovery and initialization

## Consequences

- Enables extension without modifying core logic
- Encourages a clean boundary between the core and integrations
- Requires documentation and tests for plugin discovery and registration
- Adds some indirection when tracing behavior

## Alternatives

- **Direct imports** for every adapter: simplest but not extensible
- **Entry-point only system**: powerful but adds packaging complexity early
