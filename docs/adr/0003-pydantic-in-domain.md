# ADR 0003: Use Pydantic Models in the Domain Layer

## Context

The domain module currently uses Pydantic models to enforce invariants, provide
validation, and support serialization for analytics and reporting. The hexagonal
architecture doctrine calls for framework-agnostic domain types, so we need a
documented rationale for keeping Pydantic inside the domain.

## Decision

We will keep Pydantic models in the domain layer for this codebase. The domain
models are treated as the canonical representation of test reporting facts, and
Pydantic provides reliable validation and serialization that would otherwise need
to be duplicated in adapters or application DTOs.

## Consequences

- Domain types depend on a specific framework (Pydantic), which reduces purity.
- Validation rules stay close to the domain invariants, simplifying adapter logic.
- Domain serialization is standardized for analytics and LLM payloads.
- If we later remove Pydantic, we must refactor domain models and validations.

## Alternatives

- Replace Pydantic with dataclasses and perform validation in adapters or
  application ports.
- Introduce separate DTOs in the application layer and keep the domain pure,
  using mapping at adapter boundaries.
