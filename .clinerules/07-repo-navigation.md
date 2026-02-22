# Repository navigation guidelines for hexagonal architecture

Use these guidelines to organize and discover code in hexagonal Python projects.

## Standard directory structure

### Source layout pattern
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
- `pyproject.toml` or `setup.py`: Package configuration and dependencies

## Common search patterns

### Finding definitions
```bash
# Find all class/function definitions in a specific area
rg "class|def" src/<package_name>/<area>/

# Find all ports (interfaces)
rg "class.*Protocol|@abstractmethod" src/<package_name>/application/ports/

# Find all adapters
find src/<package_name>/adapters/ -name "adapter.py" -o -name "*_adapter.py"
```

### Finding usage
```bash
# Find where a specific class is imported
rg "from.*import.*ClassName" src/ tests/

# Find instantiation of adapters
rg "new.*Adapter|Adapter\(" src/
```

### Exploring structure
```bash
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

To generate a project-specific navigation map for your repository:
1. See `.clinerules/workflows/update-repo-navigation.md` for instructions
2. Run the workflow when the project structure changes significantly
3. The generated map will provide concrete paths and file locations

## Navigation principles
- **Layer isolation**: Code in `domain/` should never import from `adapters/` or `application/`
- **Port discovery**: Look in `application/ports/` to understand system boundaries
- **Entry points**: Find wiring and configuration in entry point files (`__main__.py`, `cli.py`, or framework-specific files)
- **Test mirrors source**: Navigate tests using the same path as the source module being tested
