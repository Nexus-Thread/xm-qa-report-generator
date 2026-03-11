# Module structure and file organization

Use these rules to keep files focused, navigable, and easy to maintain.

## File size heuristics
- Treat line counts as review heuristics, not goals.
- **Should** start considering a split once a file grows beyond ~300 lines or carries more than one clear responsibility.
- Files above ~500 lines **should** have an intentional reason to remain whole.
- Files above ~700 lines **should usually** be split or accompanied by a documented justification.

## Module organization principles
- **Should** prefer cohesion and clear ownership over arbitrary file-count targets.
- **Should** use packages when a concept has multiple responsibilities or is likely to expand.
- **Should** group related classes/functions by responsibility, not by type.
- **Should** keep one primary responsibility per file/module when splitting modules.
- **Must** keep import side effects minimal; importing a module should not perform I/O, network calls, or heavyweight initialization.
- Adapter-specific structure should satisfy the architectural consistency expectations in `02-architecture-guardrails.md`.

## Package and `__init__.py` conventions
- **Should** use `__init__.py` when you want a regular package or an intentional public package API.
- Namespace packages are acceptable only when chosen deliberately and documented.
- **Must** keep `__init__.py` lightweight; avoid wiring, I/O, or hidden runtime behavior in package imports.
- **Must not** import optional/heavy dependencies in `__init__.py` only to provide a shorter import path.
- **Should** re-export symbols only when providing a stable package-level API.
- **Should** use `__all__` when a module/package has a curated public surface or needs explicit star-import semantics; it is not required in every `__init__.py`.

## Naming conventions for split modules
- Module directory: `snake_case/` (e.g., `cli_adapter/`)
- Main file: `adapter.py`, `service.py`, `writer.py`, etc. (semantic, not repetitive)
- Supporting files should prefer purpose-revealing names such as `validators.py`, `formatters.py`, `serialization.py`, `exceptions.py`, or similarly narrow modules.
- Avoid catch-all modules such as broad `utils.py`, `helpers.py`, or `common.py` unless the scope is intentionally tiny and local to the package.
- **Must** avoid redundant naming (use `cli_adapter/adapter.py`, not `cli_adapter/cli_adapter.py`)

## Adapter package mechanics
- **Must** keep sibling adapter categories internally consistent.
- **Should** use subdirectories when multiple adapters exist in the same parent directory or near-term expansion is likely.
- A single file is acceptable for a genuinely simple adapter with no near-term sibling adapters.
- **Must** name the main adapter implementation semantically, such as `adapter.py`, `parser.py`, `writer.py`, or `client.py`.
- **Must not** mix standalone files and subpackages within the same adapter category without a documented reason.

## Splitting strategies
- **Orchestration vs. implementation**: Main class in one file, helpers in others
- **By responsibility**: validators, formatters, renderers, serializers
- **By domain concept**: Each domain model in its own file
- **By layer concern**: Types, logic, utilities separate

## Import management after splits
- **Should** prefer absolute imports across package boundaries.
- Within a small local package, either absolute or relative imports are acceptable; choose one style and keep it consistent.
- Preserve public import paths only when the package intentionally exposes a stable public API.
- **Must not** create deep multi-hop re-export chains or circular imports solely for convenience.
- When backward compatibility matters, update `__init__.py` or a dedicated compatibility module intentionally and document the surface.

## When NOT to split
- Files under 200 lines that are cohesive and focused: keep them as-is.
- Simple value objects, enums, or DTOs: group related ones together.
- Tightly coupled logic that would be harder to understand when separated.
- Stable leaf modules with a single clear responsibility and no growth pressure can remain whole even if they are not tiny.

## Public API examples for intentional re-exports
- When exposing a stable package API, apply the `__init__.py` conventions above intentionally rather than re-exporting by default.
- Keep ownership visible; shorter imports are useful only when they do not create fragile or surprising import graphs.

### Re-export pattern
```python
# Optional package API: submodule/__init__.py
from .adapter import CacheAdapter
__all__ = ["CacheAdapter"]

# Parent package can re-export when the shorter import path is part of the intended API
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

# Usage when `persistence` is the intended public boundary
from myproject.adapters.output.persistence import CacheAdapter
```
