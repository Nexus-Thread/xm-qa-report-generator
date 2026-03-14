"""CLI adapter that exposes k6-oriented commands."""

import logging
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from qa_report_generator_performance.application.dtos import LlmUsageSummary
from qa_report_generator_performance.application.ports.input import (
    ExtractK6ServiceMetricsUseCase,
)
from qa_report_generator_performance.domain.exceptions import ReportingError

from .output import format_reporting_error
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
        """Generate service-specific metrics and emit logs only."""
        try:
            normalized_service = normalize_service_input(service)
            report_files = expand_report_inputs(report)
        except CliInputError as error:
            self._exit_with_error(str(error), error=error)

        LOGGER.debug(
            "CLI extraction request resolved",
            extra={
                "component": self.__class__.__name__,
                "command": "generate",
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
            self._exit_with_error(
                format_reporting_error(error),
                error=error,
                service=normalized_service,
            )

        LOGGER.info(
            "CLI extraction command completed",
            extra={
                "component": self.__class__.__name__,
                "command": "generate",
                "service": result.service,
                "report_count": len(report_files),
                "scenario_summary_count": len(result.scenario_summaries),
                "llm_usage_summary_present": result.llm_usage_summary is not None,
            },
        )
        if result.llm_usage_summary is not None:
            self._log_llm_cost_summary(service=result.service, summary=result.llm_usage_summary)

    def _exit_with_error(
        self,
        message: str,
        *,
        error: Exception | None = None,
        service: str | None = None,
    ) -> NoReturn:
        """Print formatted error and stop command execution."""
        LOGGER.error(
            "CLI extraction command failed",
            extra={
                "component": self.__class__.__name__,
                "command": "generate",
                "service": service,
                "error_type": type(error).__name__ if error is not None else "CliUsageError",
                "error_message": message,
            },
        )
        if error is None:
            raise typer.Exit(code=1)
        raise typer.Exit(code=1) from error

    def _log_llm_cost_summary(self, *, service: str, summary: LlmUsageSummary) -> None:
        """Log one structured LLM usage and cost summary."""
        LOGGER.info(
            ("LLM usage cost summary recorded: service=%s requests=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s estimated_cost_usd=%s"),
            service,
            summary.request_count,
            summary.prompt_tokens,
            summary.completion_tokens,
            summary.total_tokens,
            summary.estimated_cost_usd,
            extra={
                "component": self.__class__.__name__,
                "command": "generate",
                "service": service,
                "request_count": summary.request_count,
                "prompt_tokens": summary.prompt_tokens,
                "completion_tokens": summary.completion_tokens,
                "total_tokens": summary.total_tokens,
                "estimated_cost_usd": summary.estimated_cost_usd,
            },
        )

    def run(self) -> None:
        """Run the CLI application."""
        self.app()
