# ADR-0001: Promote reusable LLM adapters into `src/shared`

- Status: Accepted
- Date: 2026-03-13

## Context

The repository currently contains OpenAI transport and structured JSON LLM adapter code under
`src/qa_report_generator_performance/adapters/output/narrative/`.

That placement makes the implementation appear application-specific even though the same LLM
adapter stack is expected to be reused by both the performance application and a future functional
application. Keeping the reusable implementation under a single application package weakens module
ownership clarity and makes future reuse harder.

At the same time, the shared implementation must remain application-agnostic. The previous
structured adapter raised `qa_report_generator_performance.application.exceptions.
ExtractionVerificationError`, which leaked performance-app semantics into reusable code.

## Decision

Move the reusable LLM implementation into a shared adapter package at:

`src/shared/adapters/output/llm/`

This shared package owns:
- OpenAI client construction helpers
- OpenAI transport and response parsing helpers
- Shared structured JSON LLM adapter behavior
- Shared structured LLM exception types

The performance application now owns only a thin translation adapter in:

`src/qa_report_generator_performance/adapters/output/structured_llm_adapter/`

That adapter maps shared `StructuredLlmError` failures into the performance application's
`ExtractionVerificationError`, preserving application-specific error semantics at the boundary.

## Consequences

### Positive

- Reusable LLM adapter code now has an explicit shared home.
- The `adapters/output` vocabulary remains visible in both the application and shared packages.
- Future applications can reuse the same shared LLM adapter stack without importing from the
  performance package.
- Application-specific exception translation remains local to the application boundary.

### Negative

- The repository now has an additional package surface (`shared`) that must be included in build,
  import, and test configuration.
- Tests had to be split into shared adapter tests and application translation tests.

## Alternatives

### Keep the narrative module under `qa_report_generator_performance`

Rejected because it obscures the reusable nature of the LLM adapters and would force future
applications to depend on the performance package for shared infrastructure.

### Move the code to `src/shared/llm/` without adapter terminology

Rejected because the repository intentionally uses hexagonal naming, and keeping `adapters/output`
visible improves architectural clarity.

### Move the code unchanged into `src/shared`

Rejected because the previous implementation leaked performance-application exceptions into code
that should remain reusable.
