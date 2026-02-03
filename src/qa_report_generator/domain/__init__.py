"""Domain entities, value objects, and errors."""

# Exceptions - Domain-specific errors
from qa_report_generator.domain.exceptions import (
    GenerationError,
    ParseError,
    PersistenceError,
    ReportingError,
)

# Models - Business entities
from qa_report_generator.domain.models import (
    EnvironmentMeta,
    Failure,
    ReportFacts,
    RunMetrics,
    TestOutput,
)
from qa_report_generator.domain.preprocessors import (
    FailureGroup,
    FailureGrouper,
    FailurePatternExtractor,
    OutputTruncator,
)

# Value Objects - Immutable domain values
from qa_report_generator.domain.value_objects import (
    Duration,
    PassRate,
    SectionType,
    TestIdentifier,
    TestStatus,
)

__all__ = [
    "Duration",
    "EnvironmentMeta",
    "Failure",
    "FailureGroup",
    "FailureGrouper",
    "FailurePatternExtractor",
    "GenerationError",
    "OutputTruncator",
    "ParseError",
    "PassRate",
    "PersistenceError",
    "ReportFacts",
    "ReportingError",
    "RunMetrics",
    "SectionType",
    "TestIdentifier",
    "TestOutput",
    "TestStatus",
]
