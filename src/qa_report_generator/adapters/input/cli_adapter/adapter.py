"""CLI adapter that exposes k6-oriented commands."""

import logging
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from qa_report_generator.application.ports.input import (
    ExtractK6ServiceMetricsUseCase,
)
from qa_report_generator.domain.exceptions import ReportingError

from .output import build_extraction_payload, format_reporting_error, print_json_output
from .report_inputs import CliInputError, expand_report_inputs, normalize_service_input

LOGGER = logging.getLogger(__name__)


def _root_command() -> None:
    """Keep the CLI in explicit command-group mode."""


class K6CliAdapter:
    """CLI adapter that exposes k6-oriented commands."""

    def __init__(
        self,
        *,
        service_metrics_extractor: ExtractK6ServiceMetricsUseCase,
    ) -> None:
        """Initialize k6-focused CLI adapter."""
        self._service_metrics_extractor = service_metrics_extractor

        self._app = typer.Typer(
            help="Generate deterministic service metrics from k6 reports",
            add_completion=False,
        )

        self._app.callback()(_root_command)
        self._app.command(name="generate")(self.generate_command)

    @property
    def app(self) -> typer.Typer:
        """Return the Typer application."""
        return self._app

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
        """Generate and print service-specific metrics from k6 JSON reports."""
        try:
            normalized_service = normalize_service_input(service)
            report_files = expand_report_inputs(report)
        except CliInputError as error:
            self._exit_with_error(str(error), error=error)

        LOGGER.debug(
            "Resolved CLI inputs for k6 extraction",
            extra={
                "component": self.__class__.__name__,
                "service": normalized_service,
                "report_input_count": len(report),
                "resolved_report_count": len(report_files),
            },
        )

        try:
            result = self._service_metrics_extractor.extract(
                service=normalized_service,
                report_paths=report_files,
            )
        except ReportingError as error:
            self._exit_with_error(format_reporting_error(error), error=error)

        payload = build_extraction_payload(result)
        print_json_output(
            success_message="Generated service metrics",
            payload=payload,
            heading=f"Service: {result.service}",
        )

    def _exit_with_error(self, message: str, *, error: Exception | None = None) -> NoReturn:
        """Print formatted error and stop command execution."""
        LOGGER.error(
            "CLI command failed: %s",
            message,
            extra={
                "component": self.__class__.__name__,
                "error_type": type(error).__name__ if error is not None else "CliUsageError",
                "error_message": message,
            },
        )
        typer.secho(f"❌ {message}", fg=typer.colors.RED, err=True)
        if error is None:
            raise typer.Exit(code=1)
        raise typer.Exit(code=1) from error

    def run(self) -> None:
        """Run the CLI application."""
        self.app()
