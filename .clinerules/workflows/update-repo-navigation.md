# Workflow: Update Repository Navigation Map

Use this workflow to generate a project-specific navigation map when the repository structure changes significantly.

## When to run this workflow
- After major refactoring or directory restructuring
- When adding new major modules or layers
- When onboarding new team members who need a current map
- Periodically (e.g., quarterly) to keep documentation fresh

## How to run

### Option 1: Manual inspection and documentation
1. **Discover the package structure:**
   ```bash
   # Find the main package name
   ls src/

   # Show directory tree (adjust depth as needed)
   tree src/ -L 3 -d
   ```

2. **List key modules by layer:**
   ```bash
   # List domain modules
   find src/*/domain/ -name "*.py" -type f | sort

   # List application modules
   find src/*/application/ -name "*.py" -type f | sort

   # List adapters
   find src/*/adapters/ -name "*.py" -type f | sort
   ```

3. **Find entry points:**
   ```bash
   # Locate main entry points
   find src/ -name "__main__.py" -o -name "cli.py" -o -name "app.py"
   ```

4. **Document findings:**
   - Create or update a project-specific navigation file (e.g., `docs/navigation.md` or `ARCHITECTURE.md`)
   - Include actual paths and key modules discovered
   - List entry points and their purposes

### Option 2: Automated script (future enhancement)
Consider creating a Python script (e.g., `scripts/generate-nav-map.py`) that:
- Scans the `src/` directory structure
- Identifies hexagonal layers (domain, application, adapters)
- Lists key modules and classes
- Generates markdown documentation automatically
- Outputs to `docs/project-navigation.md`

**Example script structure:**
```python
#!/usr/bin/env python3
"""Generate project-specific navigation map."""
import os
from pathlib import Path

def scan_directory(path: Path, layer: str) -> list[str]:
    """Scan a layer directory and return module paths."""
    # Implementation: walk directory, find .py files, extract names
    pass

def generate_navigation_doc(package_name: str, structure: dict) -> str:
    """Generate markdown navigation documentation."""
    # Implementation: format findings as markdown
    pass

if __name__ == "__main__":
    # Scan structure
    # Generate documentation
    # Write to docs/project-navigation.md
    pass
```

## Example output format

Create a file like `docs/PROJECT-NAVIGATION.md`:

```markdown
# Project Navigation: MyProject

**Package name:** `myproject`
**Last updated:** 2026-02-03

## Source Structure
- `src/myproject/domain/` - Domain entities and business logic
  - `entities/user.py` - User entity
  - `entities/order.py` - Order entity
  - `services/pricing.py` - Pricing domain service
  - `exceptions.py` - Domain-specific exceptions

- `src/myproject/application/` - Use cases and ports
  - `use_cases/create_order.py` - Order creation workflow
  - `ports/user_repository.py` - User persistence port
  - `dtos/order_dto.py` - Order data transfer objects

- `src/myproject/adapters/` - External integrations
  - `input/cli/` - Command-line interface
  - `input/http/` - REST API handlers
  - `output/persistence/` - Database adapters
  - `output/notifications/` - Email/SMS adapters

## Entry Points
- `src/myproject/__main__.py` - CLI entry point
- `src/myproject/app.py` - Web application factory

## Test Structure
- `tests/unit/domain/` - Domain logic tests
- `tests/unit/application/` - Use case tests
- `tests/integration/adapters/` - Adapter integration tests
```

## Integration with .clinerules

After generating the project-specific map:
1. Reference it from your project's main README
2. Update `.clinerules/00-readme.md` if needed to point to the map location
3. Keep the generic guidelines in `.clinerules/07-repo-navigation.md` unchanged
4. Treat the project-specific map as living documentation, not as rules

## Tips
- Keep the navigation map in `docs/` or at the project root, not in `.clinerules/`
- Version-control the generated map so it evolves with the codebase
- Link to it from onboarding documentation
- Update it as part of major architectural changes
