# Performance vs Functional Test Report Separation

## Overview

The qa-report-generator codebase has been split to completely separate **performance** (k6) test reporting from **functional** (pytest) test reporting. This separation is implemented at the adapter, application, and domain layers while maintaining backward compatibility.

## Directory Structure

### Adapters Layer

#### Parsers
```
src/qa_report_generator/adapters/output/parsers/
├── performance/           # K6 JSON parser
│   ├── __init__.py
│   └── parser.py
├── functional/            # Pytest JSON parser
│   ├── __init__.py
│   └── parser.py
├── k6_json_parser/        # Legacy (deprecated, kept for compatibility)
└── pytest_json_parser/    # Legacy (deprecated, kept for compatibility)
```

#### Narrative Adapters
```
src/qa_report_generator/adapters/output/narrative/
├── performance/           # K6 narrative generation
│   ├── __init__.py
│   ├── narrative_adapter/
│   └── openai/
├── functional/            # Pytest narrative generation
│   ├── __init__.py
│   ├── narrative_adapter/
│   └── openai/
└── narrative_adapter/     # Legacy (deprecated, kept for compatibility)
```

#### Persistence Adapters
```
src/qa_report_generator/adapters/output/persistence/
├── performance/           # K6 report writing and caching
│   ├── __init__.py
│   ├── cache/
│   └── markdown_writer/
├── functional/            # Pytest report writing and caching
│   ├── __init__.py
│   ├── cache/
│   └── markdown_writer/
├── cache/                 # Legacy (deprecated, kept for compatibility)
└── markdown_writer/       # Legacy (deprecated, kept for compatibility)
```

### Application Layer

#### Ports
```
src/qa_report_generator/application/ports/
├── performance/           # Performance test ports (k6)
│   └── __init__.py
├── functional/            # Functional test ports (pytest)
│   └── __init__.py
└── output.py              # Shared port definitions
```

### Domain Layer

#### Models
```
src/qa_report_generator/domain/models/
├── performance/           # K6-specific models
│   └── __init__.py        # Re-exports common + K6ReportContext
├── functional/            # Pytest-specific models
│   └── __init__.py        # Re-exports common models
├── common/                # Shared models (EnvironmentMeta, Failure, etc.)
└── k6/                    # K6-specific context (K6ReportContext)
```

## Importing

### New Separated Imports

```python
# Performance (k6) imports
from qa_report_generator.adapters.output.parsers.performance import K6JsonParser
from qa_report_generator.adapters.output.narrative.performance import (
    PerformanceNarrativeAdapter, 
    PerformanceNarrativeAdapterConfig
)
from qa_report_generator.adapters.output.persistence.performance import (
    PerformanceFileReportCache,
    PerformanceMarkdownReportWriter
)
from qa_report_generator.application.ports.performance import *
from qa_report_generator.domain.models.performance import *

# Functional (pytest) imports
from qa_report_generator.adapters.output.parsers.functional import PytestJsonParser
from qa_report_generator.adapters.output.narrative.functional import (
    FunctionalNarrativeAdapter,
    FunctionalNarrativeAdapterConfig
)
from qa_report_generator.adapters.output.persistence.functional import (
    FunctionalFileReportCache,
    FunctionalMarkdownReportWriter
)
from qa_report_generator.application.ports.functional import *
from qa_report_generator.domain.models.functional import *
```

### Legacy Backward-Compatible Imports

For backward compatibility, the top-level __init__.py files still export both variants:

```python
# These still work (default to functional for non-specific imports)
from qa_report_generator.adapters.output.parsers import (
    K6JsonParser,           # From performance submodule
    PytestJsonParser        # From functional submodule
)

from qa_report_generator.adapters.output.narrative import (
    PerformanceNarrativeAdapter,
    FunctionalNarrativeAdapter,
    NarrativeAdapter        # Defaults to functional
)

from qa_report_generator.adapters.output.persistence import (
    PerformanceFileReportCache,
    FunctionalFileReportCache,
    FileReportCache         # Defaults to functional
)
```

## Design Rationale

### Why Split at This Level?

1. **Adapter Layer**: K6 and Pytest have completely different JSON output formats. Separating parsers makes it clear which parser is designed for which test framework.

2. **Narrative Layer**: While both use OpenAI for generation, the prompts, context, and metrics extracted may differ between performance and functional tests in the future.

3. **Persistence Layer**: Though currently identical, performance and functional reports may need different storage strategies (e.g., time-series databases for performance metrics vs. relational databases for test history).

4. **Application Ports**: Separating ports clarifies that each test type has its own input/output contracts.

5. **Domain Models**: Performance tests (k6) produce different metrics (throughput, latency, resource usage) than functional tests (pytest), so having separated model exports makes this explicit.

### Duplicates Are Intentional

Currently, there is code duplication between the performance and functional submodules. This is intentional because:
- It allows each track to evolve independently
- It avoids premature over-generalization
- It will be consolidated in a future refactoring once the patterns stabilize

## Future Consolidation

Once the performance and functional reporting paths are well-understood and usage patterns are clear, consider:
1. Creating a common reporting abstraction layer
2. Extracting shared logic to reduce duplication
3. Consolidating into a unified reporting framework

## Migration Guide

### For CLI Users

The CLI should eventually support routing based on test type:

```bash
# Performance test report
qa-report-generator --type performance --format k6 path/to/k6-summary.json

# Functional test report
qa-report-generator --type functional --format pytest path/to/pytest-results.json

# Auto-detect (for backward compatibility)
qa-report-generator --format k6 path/to/k6-summary.json
qa-report-generator --format pytest path/to/pytest-results.json
```

### For Library Users

Update imports to use the separated submodules:

```python
# Before (ambiguous which test type)
from qa_report_generator.adapters.output.parsers import K6JsonParser

# After (explicit about performance tests)
from qa_report_generator.adapters.output.parsers.performance import K6JsonParser
```

## Next Steps

1. ✅ Created performance/functional subdirectories in adapters, application, and domain layers
2. ✅ Copied relevant parsers, narrative adapters, and persistence adapters
3. ✅ Created __init__.py files for each submodule
4. ✅ Updated parent __init__.py files to aggregate both variants
5. ⏳ Update CLI to route to appropriate submodules based on test type
6. ⏳ Create separate use cases for performance and functional reports
7. ⏳ Update tests to cover both paths independently
8. ⏳ Document performance-specific vs functional-specific behavior
9. ⏳ Consider consolidation strategy once patterns stabilize
