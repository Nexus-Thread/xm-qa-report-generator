# Performance and observability: budgets, profiling, tracing, logging, metrics

Use these rules to keep performance regressions visible and runtime behavior traceable.

## Performance budgets
- **Should** define latency/throughput budgets for key workflows when adding new features.
- **Should** avoid introducing heavy dependencies without profiling evidence.

## Profiling expectations
- **Should** profile when changing hot paths (LLM calls, parsing, persistence).
- **Must** capture before/after numbers when optimizing.
- **Should** prefer targeted micro-benchmarks over anecdotal claims.

## Logging, tracing, and metrics
- **Should** add metrics for long-running steps (parse, LLM call, render, write).
- **Should** use tracing spans around external I/O (LLM, filesystem, APIs).

## Operational notes
- **Should** add troubleshooting notes when new failure modes are introduced.
- **Must** document new observability hooks in the README or ADRs.
