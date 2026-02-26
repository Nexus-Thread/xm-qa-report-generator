"""CLI adapter for report generation commands."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from qa_report_generator.adapters.input.cli_adapter.commands import CommandHandler
from qa_report_generator.adapters.input.cli_adapter.types import ReportFormat
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.application.ports.input import (
    CompareReportsUseCase,
    GenerateK6SummaryTableUseCase,
    GenerateReportsUseCase,
    ValidateReportUseCase,
)


class CliAdapter:
    """CLI adapter for report generation commands."""

    def __init__(
        self,
        generate_reports_use_case: GenerateReportsUseCase,
        generate_k6_summary_table_use_case: GenerateK6SummaryTableUseCase,
        compare_reports_use_case: CompareReportsUseCase,
        validate_report_use_case: ValidateReportUseCase,
        config: AppSettings,
    ) -> None:
        """Initialize CLI adapter.

        Args:
            generate_reports_use_case: Use case for report generation
            generate_k6_summary_table_use_case: Use case for consolidated k6 summary table generation
            compare_reports_use_case: Use case for report comparison
            validate_report_use_case: Use case for report input validation
            config: Configuration object

        """
        self._console = Console()
        self._command_handler = CommandHandler(
            generate_reports_use_case=generate_reports_use_case,
            generate_k6_summary_table_use_case=generate_k6_summary_table_use_case,
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
        self._app.command(name="k6-summary")(self._command_handler.k6_summary_command)
        self._app.command(name="validate-config")(self._command_handler.validate_config_command)
        self._app.command(name="diff")(self._command_handler.diff_command)

    def run(self) -> None:
        """Run the CLI application."""
        self._app()


class K6CliAdapter:
    """CLI adapter that exposes only k6-oriented commands."""

    def __init__(
        self,
        generate_reports_use_case: GenerateReportsUseCase,
        generate_k6_summary_table_use_case: GenerateK6SummaryTableUseCase,
        compare_reports_use_case: CompareReportsUseCase,
        validate_report_use_case: ValidateReportUseCase,
        config: AppSettings,
    ) -> None:
        """Initialize k6-focused CLI adapter."""
        self._console = Console()
        self._command_handler = CommandHandler(
            generate_reports_use_case=generate_reports_use_case,
            generate_k6_summary_table_use_case=generate_k6_summary_table_use_case,
            compare_reports_use_case=compare_reports_use_case,
            validate_report_use_case=validate_report_use_case,
            config=config,
            console=self._console,
        )

        self._app = typer.Typer(
            help="Generate LLM-powered test reports from k6 artifacts",
            add_completion=False,
        )
        self._app.command(name="generate")(self.generate_command)
        self._app.command(name="k6-summary")(self._command_handler.k6_summary_command)

    def generate_command(  # noqa: PLR0913
        self,
        *,
        json_report: Annotated[
            Path,
            typer.Option(
                "--json-report",
                help="Path to k6 JSON summary-export file",
                exists=True,
                file_okay=True,
                dir_okay=False,
            ),
        ],
        out: Annotated[
            Path,
            typer.Option(
                "--out",
                help="Output directory for reports",
            ),
        ] = Path("out"),
        env: Annotated[
            str | None,
            typer.Option(
                "--env",
                help="Environment name (e.g., staging, production)",
            ),
        ] = None,
        build: Annotated[
            str | None,
            typer.Option(
                "--build",
                help="Build number or ID",
            ),
        ] = None,
        commit: Annotated[
            str | None,
            typer.Option(
                "--commit",
                help="Git commit hash",
            ),
        ] = None,
        target_url: Annotated[
            str | None,
            typer.Option(
                "--target-url",
                help="Target application URL",
            ),
        ] = None,
        max_failures: Annotated[
            int,
            typer.Option(
                "--max-failures",
                help="Maximum number of failures to include (use -1 to disable limiting)",
                min=-1,
            ),
        ] = 20,
        no_llm: Annotated[
            bool,
            typer.Option(
                "--no-llm",
                help="Disable LLM narrative generation",
            ),
        ] = False,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable verbose output with detailed progress",
            ),
        ] = False,
        quiet: Annotated[
            bool,
            typer.Option(
                "--quiet",
                "-q",
                help="Minimal output (only results and errors)",
            ),
        ] = False,
        dry_run: Annotated[
            bool,
            typer.Option(
                "--dry-run",
                help="Validate inputs without generating reports",
            ),
        ] = False,
        regenerate_narratives: Annotated[
            bool,
            typer.Option(
                "--regenerate-narratives",
                help="Reuse cached parsed metrics and regenerate only LLM narratives",
            ),
        ] = False,
        profile: Annotated[
            str | None,
            typer.Option(
                "--profile",
                help="Preprocessing profile preset (minimal, balanced, detailed)",
            ),
        ] = None,
    ) -> None:
        """Generate k6 test summary and QA sign-off reports."""
        self._command_handler.generate_command(
            json_report=json_report,
            out=out,
            env=env,
            build=build,
            commit=commit,
            target_url=target_url,
            max_failures=max_failures,
            no_llm=no_llm,
            verbose=verbose,
            quiet=quiet,
            dry_run=dry_run,
            regenerate_narratives=regenerate_narratives,
            profile=profile,
            report_fmt=ReportFormat.K6,
        )

    def run(self) -> None:
        """Run the CLI application."""
        self._app()
