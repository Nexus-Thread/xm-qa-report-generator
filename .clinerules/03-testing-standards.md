# Testing standards: pyramid, pytest conventions, fixtures, mocks, coverage

Use these rules for all automated tests to keep signal high and feedback fast.

**For test directory structure and organization, see `07-repo-navigation.md`.**

## Test pyramid expectations
- **Must** keep the majority of tests as unit tests (fast, isolated, no I/O).
- **Should** use integration tests sparingly for adapter boundaries that touch real I/O.
- **Must** avoid mixing adapter behavior into domain unit tests.

## Pytest conventions
- **Must** name tests `test_<behavior>()` with clear, behavior-oriented names.
- **Must** use `pytest` fixtures for shared setup; avoid module-level globals.
- **Should** use markers (`@pytest.mark.slow`, `@pytest.mark.integration`) for long-running suites.
- **Must** keep assertions focused on observable outcomes, not implementation details.

## Mocks, stubs, and fakes
- **Must** mock output ports in application tests to verify orchestration.
- **Must** avoid mocking domain entities or value objects.
- **Should** use fakes for external dependencies when deterministic behavior is needed.

## Coverage and regression expectations
- **Must** add or update tests when behavior changes.
- **Should** add regression tests for bugs before fixing them.
- **Should** keep coverage stable or improving; document intentional gaps in PR notes.

## Running tests
- **Should** run a focused subset during development.
- **Must** run the full suite (`pytest tests/`) before handoff or PR.
