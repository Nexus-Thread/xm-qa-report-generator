"""CLI output helpers for k6 extraction commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator_performance.application.dtos import K6ServiceExtractionResult
    from qa_report_generator_performance.domain.exceptions import ReportingError


def format_reporting_error(error: ReportingError) -> str:
    """Build CLI-facing text for a reporting error."""
    suggestion = f"\n💡 Suggestion: {error.suggestion}" if error.suggestion else ""
    return f"{error}{suggestion}"


def build_extraction_payload(
    result: K6ServiceExtractionResult,
) -> dict[str, object]:
    """Build extraction JSON payload for CLI consumers or tests."""
    return result.to_summary_payload()
