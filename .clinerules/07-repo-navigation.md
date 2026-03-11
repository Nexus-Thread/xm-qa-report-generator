# Repository navigation guidelines for hexagonal architecture

Use these guidelines to organize and discover code in hexagonal Python projects.

## Standard directory structure

### Source layout pattern
Prefer a `src/<package_name>/` layout for libraries and reusable services. Smaller applications may use `<package_name>/` at the project root if packaging and test imports remain clear.

In monorepos, repeat this mental model per package/service and keep package-local entry points, tests, and docs discoverable near each package root.

```
src/<package_name>/
├── domain/                  # Core business logic
│   ├── entities/           # Domain entities
│   ├── value_objects/      # Immutable value objects
│   ├── services/           # Domain services
│   └── exceptions.py       # Domain-specific errors
├── application/            # Use cases and orchestration
│   ├── use_cases/          # Application use cases
│   ├── ports/              # Input/output ports (interfaces)
│   └── dtos/               # Data transfer objects
└── adapters/               # External system interfaces
    ├── input/              # Driving adapters (CLI, HTTP, GraphQL)
    └── output/             # Driven adapters (DB, APIs, messaging)
```

### Test layout pattern
```
tests/
├── unit/                   # Fast, isolated unit tests
│   ├── domain/            # Domain logic tests
│   ├── application/       # Use case tests
│   └── adapters/          # Adapter unit tests
├── integration/           # Integration tests with I/O
│   └── adapters/          # Adapter integration tests
└── e2e/                   # Optional end-to-end scenarios
```

**Note:** Test directories should mirror the source structure for easy navigation. `e2e/` may be organized by user flow instead of strict source mirroring.

## Documentation and configuration
- `README.md`: Project onboarding, setup, and usage
- `docs/`: Architecture decision records (ADRs), design docs
- `examples/`: Runnable code examples and integration snippets
- `pyproject.toml`: Primary package, build, dependency, and tool configuration
- `uv.lock`: Locked dependency state for the project

## Common search patterns

### Finding definitions
```bash
# Find all class/function definitions in a specific area
rg "^\s*(class|def)\s+" src/<package_name>/<area>/

# Find all ports (interfaces)
rg "Protocol|ABC|abstractmethod" src/<package_name>/application/ports/

# Find all adapters
find src/<package_name>/adapters/ -name "adapter.py" -o -name "*_adapter.py"
```

### Finding usage
```bash
# Find where a specific class is imported
rg "from .* import ClassName|import .*ClassName" src/ tests/

# Find adapter instantiation or wiring
rg "\b[A-Z][A-Za-z0-9_]*Adapter\(" src/
```

### Exploring structure
```bash
# Find package roots or service roots in a monorepo
find . -name "pyproject.toml"

# View directory tree
tree src/<package_name>/ -L 3

# Fallback if tree is unavailable
find src/<package_name>/ -maxdepth 3 -type d

# List all Python files in a layer
find src/<package_name>/domain/ -name "*.py"

# Find entry points (CLI, main modules)
find src/ -name "__main__.py" -o -name "cli.py"
```

## Project-specific navigation

To generate a project-specific navigation map for your project:
1. See `workflows/update-repo-navigation.md` for instructions
2. Run the workflow when the project structure changes significantly
3. Store the generated map in `docs/repo-navigation.md` or a similarly discoverable project-specific location outside `.clinerules/`

## Navigation principles
- **Layer isolation**: Code in `domain/` should never import from `adapters/` or `application/`
- **Port discovery**: Look in `application/ports/` to understand system boundaries
- **Entry points**: Find wiring and configuration in entry point files (`__main__.py`, `cli.py`, or framework-specific bootstrap modules)
- **Packaging clues**: Start with `pyproject.toml` and `uv.lock` to identify package roots, toolchain, and supported Python versions
- **Test mirrors source**: Navigate tests using the same path as the source module being tested
