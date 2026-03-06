# Module structure and file organization

Use these rules to keep files focused, navigable, and easy to maintain.

## File size limits
- **Must** keep individual files under 300 lines when possible.
- **Should** split files exceeding 400 lines into focused modules.
- **Must** split files exceeding 600 lines unless there's a strong justification.

## Module organization principles
- **Should** use directories with multiple files instead of large single-file modules.
- **Must** use `__init__.py` to expose public API; keep internal implementation private.
- **Should** group related classes/functions by responsibility, not by type.
- **Must** keep one primary class/responsibility per file when splitting modules.
- Adapter-specific structure should satisfy the architectural consistency expectations in `02-architecture-guardrails.md`.

## Naming conventions for split modules
- Module directory: `snake_case/` (e.g., `cli_adapter/`)
- Main file: `adapter.py`, `service.py`, `writer.py`, etc. (semantic, not repetitive)
- Supporting files: `types.py`, `validators.py`, `formatters.py`, `utils.py`, etc.
- **Must** avoid redundant naming (use `cli_adapter/adapter.py`, not `cli_adapter/cli_adapter.py`)

## Adapter package mechanics
- **Must** organize adapters in subdirectories when multiple adapters exist in the same parent directory.
- **Should** use subdirectories even for simple, single-file adapters to preserve consistent expansion paths.
- **Must** name the main adapter implementation semantically, such as `adapter.py`, `parser.py`, `writer.py`, or `client.py`.
- **Must** keep adapter categories internally consistent instead of mixing standalone files and subpackages without a documented reason.
- When there is only one adapter in a category and no near-term expectation of siblings, a single file may be acceptable if the reasoning is documented.

## Splitting strategies
- **Orchestration vs. implementation**: Main class in one file, helpers in others
- **By responsibility**: validators, formatters, renderers, serializers
- **By domain concept**: Each domain model in its own file
- **By layer concern**: Types, logic, utilities separate

## Import management after splits
- **Must** update `__init__.py` to maintain backward compatibility during refactoring.
- **Should** use relative imports within the same package.
- **Must** keep public API stable; internal reorganization should be transparent to consumers.

## When NOT to split
- Files under 200 lines that are cohesive and focused: keep them as-is.
- Simple value objects, enums, or DTOs: group related ones together.
- Tightly coupled logic that would be harder to understand when separated.

## Public API and `__init__.py` conventions
- **Must** re-export public classes/functions from subdirectory `__init__.py` to parent `__init__.py`
- **Must** use `__all__` to explicitly define the public API in each `__init__.py`
- **Should** keep imports short and clean by leveraging the re-export chain
- **Must** avoid forcing consumers to import from deeply nested paths

### Re-export pattern
```python
# Innermost: submodule/__init__.py
from .adapter import CacheAdapter
__all__ = ["CacheAdapter"]

# Parent: parent/__init__.py
from .submodule import CacheAdapter
from .other_submodule import OtherClass
__all__ = ["CacheAdapter", "OtherClass"]
```

### Example: persistence adapters
```python
# persistence/cache/__init__.py
from .adapter import CacheAdapter
__all__ = ["CacheAdapter"]

# persistence/database/__init__.py
from .adapter import DatabaseAdapter
__all__ = ["DatabaseAdapter"]

# persistence/__init__.py
from .cache import CacheAdapter
from .database import DatabaseAdapter
__all__ = ["CacheAdapter", "DatabaseAdapter"]

# Usage (clean, short import)
from myproject.adapters.output.persistence import CacheAdapter
```
