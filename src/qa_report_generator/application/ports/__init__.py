"""Application port interfaces."""

# Input Ports
from qa_report_generator.application.ports.input import (
    CompareReportsUseCase,
    GenerateReportsUseCase,
    ReportGenerationResult,
)

# Output Ports
from qa_report_generator.application.ports.output import (
    NarrativeGenerator,
    ReportCache,
    ReportParser,
    ReportWriter,
)

__all__ = [
    "CompareReportsUseCase",
    "GenerateReportsUseCase",
    "NarrativeGenerator",
    "ReportCache",
    "ReportGenerationResult",
    "ReportParser",
    "ReportWriter",
]
