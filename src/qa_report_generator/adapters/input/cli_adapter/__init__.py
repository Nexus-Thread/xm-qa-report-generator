"""CLI adapter module for report generation."""

from qa_report_generator.adapters.input.cli_adapter.adapter import CliAdapter
from qa_report_generator.adapters.input.cli_adapter.types import (
    GenerationResult,
    OutputVerbosity,
    ReportOptions,
)

__all__ = [
    "CliAdapter",
    "GenerationResult",
    "OutputVerbosity",
    "ReportOptions",
]
