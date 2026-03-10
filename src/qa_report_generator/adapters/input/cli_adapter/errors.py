"""CLI-specific errors and error formatting helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.domain.exceptions import ReportingError


class CliInputError(ValueError):
    """Raised when CLI input validation fails."""


def format_reporting_error(error: ReportingError) -> str:
    """Build CLI-facing text for a reporting error."""
    suggestion = f"\n💡 Suggestion: {error.suggestion}" if error.suggestion else ""
    return f"{error}{suggestion}"
