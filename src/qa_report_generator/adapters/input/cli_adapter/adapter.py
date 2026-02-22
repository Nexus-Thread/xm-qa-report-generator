"""CLI adapter for report generation commands."""

import typer
from rich.console import Console

from qa_report_generator.adapters.input.cli_adapter.commands import CommandHandler
from qa_report_generator.application.ports.input import (
    CompareReportsUseCase,
    GenerateReportsUseCase,
    ValidateReportUseCase,
)
from qa_report_generator.config import Config


class CliAdapter:
    """CLI adapter for report generation commands."""

    def __init__(
        self,
        generate_reports_use_case: GenerateReportsUseCase,
        compare_reports_use_case: CompareReportsUseCase,
        validate_report_use_case: ValidateReportUseCase,
        config: Config | None = None,
    ) -> None:
        """Initialize CLI adapter.

        Args:
            generate_reports_use_case: Use case for report generation
            compare_reports_use_case: Use case for report comparison
            validate_report_use_case: Use case for report input validation
            config: Configuration object (optional, for validation command)

        """
        self._console = Console()
        self._command_handler = CommandHandler(
            generate_reports_use_case=generate_reports_use_case,
            compare_reports_use_case=compare_reports_use_case,
            validate_report_use_case=validate_report_use_case,
            config=config,
            console=self._console,
        )

        self._app = typer.Typer(
            help="Generate LLM-powered test reports from pytest artifacts",
            add_completion=False,
        )
        self._app.command(name="generate")(self._command_handler.generate_command)
        self._app.command(name="validate-config")(self._command_handler.validate_config_command)
        self._app.command(name="diff")(self._command_handler.diff_command)

    def run(self) -> None:
        """Run the CLI application."""
        self._app()
