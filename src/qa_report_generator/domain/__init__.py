"""Domain entities, value objects, and errors."""

# Exceptions - Domain-specific errors
from qa_report_generator.domain.exceptions import (
    ConfigurationError,
    GenerationError,
    ParseError,
    ParseFileNotFoundError,
    ParseInvalidFormatError,
    ParseInvalidJsonError,
    PersistenceError,
    ReportingError,
)

# Models - Business entities
from qa_report_generator.domain.models import (
    EnvironmentMeta,
    Failure,
    K6Check,
    K6ReportContext,
    K6Threshold,
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
    "ConfigurationError",
    "Duration",
    "EnvironmentMeta",
    "Failure",
    "FailureGroup",
    "FailureGrouper",
    "FailurePatternExtractor",
    "GenerationError",
    "K6Check",
    "K6ReportContext",
    "K6Threshold",
    "OutputTruncator",
    "ParseError",
    "ParseFileNotFoundError",
    "ParseInvalidFormatError",
    "ParseInvalidJsonError",
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
