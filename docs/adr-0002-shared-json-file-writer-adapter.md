# ADR-0002: Promote JSON file writer adapter into `src/shared`

- Status: Accepted
- Date: 2026-03-13

## Context

`JsonFileWriterAdapter` was located under
`src/qa_report_generator_performance/adapters/output/persistence/`, but its behavior is generic:
it normalizes common Python values into JSON and persists them to timestamped files.

The adapter does not encode k6, performance-reporting, or application-specific semantics. It is a
generic persistence adapter that can be reused by multiple applications in this repository.

## Decision

Move `JsonFileWriterAdapter` into:

`src/shared/adapters/output/persistence/json_file_writer_adapter/`

The performance application will import it from shared code rather than owning the implementation
locally.

## Consequences

### Positive

- Reusable JSON persistence logic has a clear shared home.
- Future applications can reuse the same file-writer adapter without depending on the performance
  package.
- Shared adapter tests now validate this behavior in the shared test tree.

### Negative

- Imports must be updated where the performance app previously referenced the local persistence
  adapter.
- The repository gains another shared adapter package to maintain.

## Alternatives

### Keep the adapter inside `qa_report_generator_performance`

Rejected because the adapter is generic infrastructure rather than performance-specific behavior.

### Keep a full duplicate implementation in both app and shared code

Rejected because it would create maintenance drift for no architectural benefit.
