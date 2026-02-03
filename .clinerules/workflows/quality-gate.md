# Quality Gate Workflow

Run this before handoff, PR creation, or at the end of any coding session.

## Commands

```bash
# Step 1: Format & Auto-fix
ruff format .
ruff check . --fix

# Step 2: Lint
ruff check .

# Step 3: Type check
mypy src/ tests/

# Step 4: Tests
pytest tests/
```

## Quick reference (all steps chained)

```bash
ruff format . && ruff check . --fix && ruff check . && mypy src/ tests/ && pytest tests/
```

---

See `.clinerules/09-tooling-and-ci.md` for detailed expectations and usage clarifications.
