"""CLI adapter that exposes k6-oriented commands."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, NoReturn, TypeVar

import typer

from qa_report_generator.application.dtos import K6ServiceExtractionResult
from qa_report_generator.application.ports.input import (
    ExtractK6ServiceMetricsUseCase,
)
from qa_report_generator.domain.exceptions import ReportingError

_RESULT = TypeVar("_RESULT")


class K6CliAdapter:
    """CLI adapter that exposes k6-oriented commands."""

    def __init__(
        self,
        extract_k6_service_metrics_use_case: ExtractK6ServiceMetricsUseCase,
    ) -> None:
        """Initialize k6-focused CLI adapter."""
        self._extract_k6_service_metrics_use_case = extract_k6_service_metrics_use_case

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

        return sorted(resolved_files)

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
    ) -> None:
        """Generate and print service-specific deterministic metrics from one or more k6 JSON reports."""
        normalized_service = self._normalize_service(service)
        report_files = self._resolve_report_files(report)
        result = self._execute_or_exit(
            lambda: self._extract_k6_service_metrics_use_case.extract(
                service=normalized_service,
                report_paths=report_files,
            )
        )
        payload = self._build_extraction_payload(result)
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

    def _build_extraction_payload(self, result: K6ServiceExtractionResult) -> dict[str, object]:
        """Build extraction JSON payload for CLI output."""
        return {
            "service": result.service,
            "mode": result.mode,
            "extracted_runs": [
                {
                    "report_file": run.report_file,
                    "extracted": run.extracted,
                }
                for run in result.extracted_runs
            ],
        }

    def _execute_or_exit(self, operation: Callable[[], _RESULT]) -> _RESULT:
        """Execute operation and convert domain/system errors to CLI exits."""
        try:
            return operation()
        except ReportingError as error:
            suggestion = f"\n💡 Suggestion: {error.suggestion}" if error.suggestion else ""
            self._exit_with_error(f"{error}{suggestion}", error=error)
        except Exception as error:
            self._exit_with_error(f"Error: {error}", error=error)

    def _print_json_output(self, *, success_message: str, payload: object, heading: str | None = None) -> None:
        """Print success text and JSON payload."""
        typer.secho(f"✅ {success_message}", fg=typer.colors.GREEN)
        if heading:
            typer.echo(heading)
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))

    def _exit_with_error(self, message: str, *, error: Exception | None = None) -> NoReturn:
        """Print formatted error and stop command execution."""
        typer.secho(f"❌ {message}", fg=typer.colors.RED)
        if error is None:
            raise typer.Exit(code=1)
        raise typer.Exit(code=1) from error

    def run(self) -> None:
        """Run the CLI application."""
        self._app()
