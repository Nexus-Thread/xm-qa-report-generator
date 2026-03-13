"""CLI output helpers for k6 extraction commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import typer

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
    """Build extraction JSON payload for CLI output."""
    return result.to_summary_payload()


def print_json_output(*, success_message: str, payload: object, heading: str | None = None) -> None:
    """Print success text and JSON payload."""
    typer.secho(f"✅ {success_message}", fg=typer.colors.GREEN)
    if heading:
        typer.echo(heading)
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
