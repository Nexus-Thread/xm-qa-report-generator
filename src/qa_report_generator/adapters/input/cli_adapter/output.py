"""CLI output helpers for k6 extraction commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import typer

if TYPE_CHECKING:
    from qa_report_generator.application.dtos import K6ServiceExtractionResult
    from qa_report_generator.domain.exceptions import ReportingError


def format_reporting_error(error: ReportingError) -> str:
    """Build CLI-facing text for a reporting error."""
    suggestion = f"\n💡 Suggestion: {error.suggestion}" if error.suggestion else ""
    return f"{error}{suggestion}"


def build_extraction_payload(
    result: K6ServiceExtractionResult,
) -> dict[str, object]:
    """Build extraction JSON payload for CLI output."""
    return {
        "service": result.service,
        "mode": result.mode,
        "overall_summary": {
            "status": result.overall_summary.status,
            "total_scenarios": result.overall_summary.total_scenarios,
            "passed_scenarios": result.overall_summary.passed_scenarios,
            "failed_scenarios": result.overall_summary.failed_scenarios,
            "unknown_scenarios": result.overall_summary.unknown_scenarios,
            "scenarios_requiring_attention": result.overall_summary.scenarios_requiring_attention,
            "executive_summary": result.overall_summary.executive_summary,
        },
        "scenario_summaries": [
            {
                "scenario_name": summary.scenario_name,
                "env_name": summary.env_name,
                "source_report_files": summary.source_report_files,
                "status": summary.status,
                "executor": summary.executor,
                "rate": summary.rate,
                "duration": summary.duration,
                "pre_allocated_vus": summary.pre_allocated_vus,
                "max_vus": summary.max_vus,
                "threshold_results": [
                    {
                        "metric_key": threshold.metric_key,
                        "expression": threshold.expression,
                        "status": threshold.status,
                    }
                    for threshold in summary.threshold_results
                ],
                "executive_note": summary.executive_note,
            }
            for summary in result.scenario_summaries
        ],
    }


def print_json_output(*, success_message: str, payload: object, heading: str | None = None) -> None:
    """Print success text and JSON payload."""
    typer.secho(f"✅ {success_message}", fg=typer.colors.GREEN)
    if heading:
        typer.echo(heading)
    typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
