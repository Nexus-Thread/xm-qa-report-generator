"""CLI adapter that exposes k6-oriented commands."""

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal, NoReturn, TypeVar

import typer

from qa_report_generator.application.dtos import K6ServiceExtractionResult
from qa_report_generator.application.ports.input import (
    ExtractK6ServiceMetricsUseCase,
)
from qa_report_generator.application.ports.output import DebugJsonWriterPort
from qa_report_generator.domain.exceptions import ReportingError

OutputMode = Literal["summary", "full"]

_RESULT = TypeVar("_RESULT")
LOGGER = logging.getLogger(__name__)


class K6CliAdapter:
    """CLI adapter that exposes k6-oriented commands."""

    def __init__(
        self,
        extract_k6_service_metrics_use_case: ExtractK6ServiceMetricsUseCase,
        output_mode: OutputMode = "summary",
        model_debug_json_writer: DebugJsonWriterPort | None = None,
        model_debug_json_enabled: bool = False,
    ) -> None:
        """Initialize k6-focused CLI adapter."""
        self._extract_k6_service_metrics_use_case = extract_k6_service_metrics_use_case
        self._output_mode = output_mode
        self._model_debug_json_writer = model_debug_json_writer
        self._model_debug_json_enabled = model_debug_json_enabled

        self._app = typer.Typer(
            help="Generate deterministic service metrics from k6 reports",
            add_completion=False,
        )

        self._app.callback()(self.root_command)
        self._app.command(name="generate")(self.generate_command)

    def root_command(self) -> None:
        """Define CLI root to keep command-group behavior with explicit subcommands."""

    def _resolve_report_files(self, report_inputs: list[Path]) -> list[Path]:
        """Resolve report inputs into a de-duplicated file list."""
        if not report_inputs:
            self._exit_with_error("At least one --report input is required")

        resolved_files: set[Path] = set()

        for report_input in report_inputs:
            resolved_files.update(self._expand_report_input(report_input))

        sorted_files = sorted(resolved_files)
        LOGGER.debug(
            "Resolved report inputs for CLI extraction",
            extra={
                "component": self.__class__.__name__,
                "report_input_count": len(report_inputs),
                "resolved_report_count": len(sorted_files),
            },
        )
        return sorted_files

    def _expand_report_input(self, report_input: Path) -> list[Path]:
        """Expand one report input into concrete JSON files."""
        if report_input.is_dir():
            directory_files = sorted(path for path in report_input.glob("*.json") if path.is_file())
            if not directory_files:
                self._exit_with_error(f"No JSON report files found in directory: {report_input}")
            return directory_files

        if report_input.is_file():
            if report_input.suffix.lower() != ".json":
                self._exit_with_error(f"Report file must be a JSON file: {report_input}")
            return [report_input]

        self._exit_with_error(f"Invalid report input: {report_input}")
        msg = "Unreachable"
        raise AssertionError(msg)

    def generate_command(
        self,
        *,
        service: Annotated[
            str,
            typer.Option(
                "--service",
                help="Service identifier for extraction schema selection",
            ),
        ],
        report: Annotated[
            list[Path],
            typer.Option(
                "--report",
                help="k6 JSON file or directory containing k6 JSON files (repeat for multiple inputs)",
                exists=True,
                file_okay=True,
                dir_okay=True,
            ),
        ],
        output: Annotated[
            OutputMode | None,
            typer.Option(
                "--output",
                help="Output mode: 'summary' for executive summary only or 'full' for detailed runs",
            ),
        ] = None,
    ) -> None:
        """Generate and print service-specific deterministic metrics from one or more k6 JSON reports."""
        normalized_service = self._normalize_service(service)
        report_files = self._resolve_report_files(report)
        output_mode = output or self._output_mode
        result = self._execute_or_exit(
            lambda: self._extract_k6_service_metrics_use_case.extract(
                service=normalized_service,
                report_paths=report_files,
            )
        )
        payload = self._build_extraction_payload(result, output_mode=output_mode)
        self._write_model_debug_payload(payload=payload, output_mode=output_mode)
        self._print_json_output(
            success_message="Generated service metrics",
            payload=payload,
            heading=f"Service: {result.service}",
        )

    def _normalize_service(self, service: str) -> str:
        """Normalize and validate service identifier input."""
        normalized_service = service.strip()
        if not normalized_service:
            self._exit_with_error("--service cannot be empty")
        return normalized_service

    def _build_extraction_payload(
        self,
        result: K6ServiceExtractionResult,
        *,
        output_mode: OutputMode,
    ) -> dict[str, object]:
        """Build extraction JSON payload for CLI output."""
        summary_payload: dict[str, object] = {
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
        if output_mode == "summary":
            return summary_payload

        return {
            **summary_payload,
            "runs": [
                {
                    "source_report_files": run.source_report_files,
                    "extracted": run.extracted,
                }
                for run in result.runs
            ],
        }

    def _write_model_debug_payload(self, *, payload: object, output_mode: OutputMode) -> None:
        """Persist final model payload when model JSON debug output is enabled."""
        if not self._model_debug_json_enabled or self._model_debug_json_writer is None:
            return

        try:
            if output_mode == "full":
                self._model_debug_json_writer.write_json(
                    label="full_output",
                    payload=payload,
                )
        except (OSError, TypeError, ValueError) as err:
            LOGGER.warning(
                "Failed to write model debug payload",
                exc_info=err,
                extra={
                    "component": self.__class__.__name__,
                    "output_mode": output_mode,
                },
            )

    def _execute_or_exit(self, operation: Callable[[], _RESULT]) -> _RESULT:
        """Execute operation and convert domain/system errors to CLI exits."""
        try:
            return operation()
        except ReportingError as error:
            self._exit_with_error(self._format_reporting_error_message(error), error=error)

    def _format_reporting_error_message(self, error: ReportingError) -> str:
        """Build CLI-facing error text from a reporting error."""
        suggestion = f"\n💡 Suggestion: {error.suggestion}" if error.suggestion else ""
        return f"{error}{suggestion}"

    def _print_json_output(self, *, success_message: str, payload: object, heading: str | None = None) -> None:
        """Print success text and JSON payload."""
        typer.secho(f"✅ {success_message}", fg=typer.colors.GREEN)
        if heading:
            typer.echo(heading)
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

    def _exit_with_error(self, message: str, *, error: Exception | None = None) -> NoReturn:
        """Print formatted error and stop command execution."""
        LOGGER.error(
            "CLI command failed",
            extra={
                "component": self.__class__.__name__,
                "error_type": type(error).__name__ if error is not None else "CliUsageError",
            },
        )
        typer.secho(f"❌ {message}", fg=typer.colors.RED)
        if error is None:
            raise typer.Exit(code=1)
        raise typer.Exit(code=1) from error

    def run(self) -> None:
        """Run the CLI application."""
        self._app()
