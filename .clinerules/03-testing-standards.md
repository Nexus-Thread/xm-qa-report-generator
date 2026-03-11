# Testing standards: pyramid, pytest conventions, fixtures, mocks, coverage

Use these rules for all automated tests to keep signal high and feedback fast.

**For test directory structure and organization, see `07-repo-navigation.md`.**

## Test pyramid expectations
- **Must** keep the majority of tests as unit tests (fast, isolated, no I/O).
- **Should** use integration tests sparingly for adapter boundaries that touch real I/O.
- **Should** add contract tests around important ports/adapters when multiple implementations must honor the same behavior.
- **Must** avoid mixing adapter behavior into domain unit tests.

## Test quality defaults
- **Must** keep tests deterministic and isolated; avoid hidden reliance on wall clock time, randomness, ambient environment variables, or test order.
- **Should** control time, randomness, filesystem, and network behavior explicitly through fixtures, fakes, or test helpers.
- **Should** prefer small builders/factories over large shared fixtures when setup starts hiding the behavior under test.
- **Must not** rely on live external services in the default local or CI test suite.

## Pytest conventions
- **Must** name tests `test_<behavior>()` with clear, behavior-oriented names.
- **Must** use `pytest` fixtures for shared setup; avoid module-level globals.
- **Should** use `@pytest.mark.parametrize` for behavior matrices instead of repetitive copy-pasted tests.
- **Should** use markers (`@pytest.mark.slow`, `@pytest.mark.integration`) for long-running suites.
- **Must** keep assertions focused on observable outcomes, not implementation details.

## Mocks, stubs, and fakes
- **Must** mock output ports in application tests to verify orchestration.
- **Must** avoid mocking domain entities or value objects.
- **Should** use fakes for external dependencies when deterministic behavior is needed.
- **Should** prefer fakes or thin test doubles over deep mock chains that mirror implementation details.
- When multiple adapters implement the same important port, **should** define shared contract tests that each implementation must satisfy.

## Async and boundary testing
- **Should** use `pytest-asyncio` consistently when testing async code.
- **Must** isolate real network, filesystem, and database access to explicit integration/e2e tests.
- **Should** use temporary directories, ephemeral databases, or sandbox resources instead of shared developer state.

## Coverage and regression expectations
- **Must** add or update tests when behavior changes.
- **Should** add regression tests for bugs before fixing them.
- **Should** add property-based tests (for example with Hypothesis) or edge-case matrix tests for domain invariants and parser/serializer boundaries when the input space is broad.
- **Should** keep coverage stable or improving; document intentional gaps in PR notes.

## Running tests
- **Should** run a focused `uv run pytest tests/...` or `uv run pytest -k <pattern>` subset during development.
- **Must** run `uv run pytest` before handoff or PR.
- **Should** keep slow/integration/e2e suites clearly marked so the fast default developer loop stays intentional.
- **Must** follow the full local quality gate order in `09-tooling-and-ci.md` before handoff.
