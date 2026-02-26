"""Application port interfaces."""

# Input Ports
from qa_report_generator.application.ports.input import (
    CompareReportsUseCase,
    GenerateK6SummaryTableUseCase,
    GenerateReportsUseCase,
    K6SummaryTableResult,
    ReportGenerationResult,
    ValidateReportUseCase,
)

# Output Ports
from qa_report_generator.application.ports.output import (
    K6SummaryParser,
    K6SummaryWriter,
    NarrativeGenerator,
    ReportCache,
    ReportParser,
    ReportWriter,
)

__all__ = [
    "CompareReportsUseCase",
    "GenerateK6SummaryTableUseCase",
    "GenerateReportsUseCase",
    "K6SummaryParser",
    "K6SummaryTableResult",
    "K6SummaryWriter",
    "NarrativeGenerator",
    "ReportCache",
    "ReportGenerationResult",
    "ReportParser",
    "ReportWriter",
    "ValidateReportUseCase",
]
