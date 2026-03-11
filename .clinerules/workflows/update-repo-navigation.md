# Workflow: update project navigation map

Use this workflow when adapting the reusable hexagonal Python ruleset to a specific project.

## Goal
Produce a short, project-specific navigation guide outside `.clinerules/` so contributors can find package roots, entry points, adapters, and tests quickly.

## Recommended output location
- `docs/repo-navigation.md`
- or another discoverable project-owned path near the main developer docs

## Steps
1. Identify the package root (`src/<package_name>/` or the top-level package directory).
2. Locate entry points and composition-root/bootstrap files (`__main__.py`, `cli.py`, ASGI/WSGI app factories, worker startup modules, etc.).
3. Map the hexagonal layers:
   - `domain/`
   - `application/`
   - `adapters/input/`
   - `adapters/output/`
   - shared infrastructure/bootstrap modules, if present
4. Map the test layout (`tests/unit/`, `tests/integration/`, `tests/e2e/`, shared fixtures, contract tests).
5. Record the most useful project-specific search commands for ports, adapters, entry points, and tests.
6. Save the navigation guide outside `.clinerules/` and update it whenever structure changes materially.

## Suggested template
```md
# Project navigation

## Package roots
- `src/myproject/`

## Entry points / composition root
- `src/myproject/cli.py`
- `src/myproject/bootstrap.py`

## Domain
- `src/myproject/domain/`

## Application
- `src/myproject/application/`

## Adapters
- Input: `src/myproject/adapters/input/`
- Output: `src/myproject/adapters/output/`

## Tests
- Unit: `tests/unit/`
- Integration: `tests/integration/`
- E2E: `tests/e2e/`

## Useful search commands
- `rg "Protocol|ABC|abstractmethod" src/myproject/application/ports/`
- `find src/myproject/adapters/ -name "adapter.py" -o -name "*_adapter.py"`
```
