# Logging conventions: module-level logger standard and exceptions

Use these rules to keep logging consistent and filterable across modules.

## Default logger pattern
- **Must** define a module-level logger in any module that emits logs:
  - `LOGGER = logging.getLogger(__name__)`
- **Must** use the module-level `LOGGER` inside functions and class methods.
- **Must not** create per-instance loggers like `self._logger` by default.

## Context and structure
- **Should** include structured context via `extra={...}` for operational logs.
- **Should** include `component` or equivalent context when class attribution is useful.
- **Must** keep logger names hierarchical by using `__name__` to support selective filtering.

## Exceptions
- **May** use instance-specific loggers only when behavior requires runtime logger names or explicit logger injection.
- **Must** document the reason in a short inline comment when deviating from the default pattern.

## Central configuration
- **Must** configure logging through the central logging configuration utilities.
- **Must not** duplicate global logging setup in feature modules.
