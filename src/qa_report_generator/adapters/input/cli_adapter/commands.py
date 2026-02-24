"""Command implementations for CLI adapter."""

import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from qa_report_generator.adapters.input.cli_adapter.formatters import ConsoleFormatter
from qa_report_generator.adapters.input.cli_adapter.progress import ProgressTracker
from qa_report_generator.adapters.input.cli_adapter.types import (
    GenerationResult,
    OutputVerbosity,
    ReportOptions,
)
from qa_report_generator.adapters.input.cli_adapter.utils import apply_profile, resolve_verbosity
from qa_report_generator.adapters.input.cli_adapter.validators import InputValidator
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.application.ports.input import (
    CompareReportsUseCase,
    GenerateReportsUseCase,
    ValidateReportUseCase,
)
from qa_report_generator.domain.analytics.models import ReportDiff
from qa_report_generator.domain.exceptions import ReportingError
from qa_report_generator.domain.models import EnvironmentMeta


class CommandHandler:
    """Handles CLI command execution."""

    def __init__(
        self,
        generate_reports_use_case: GenerateReportsUseCase,
        compare_reports_use_case: CompareReportsUseCase,
        validate_report_use_case: ValidateReportUseCase,
        config: AppSettings,
        console: Console,
    ) -> None:
        """Initialize command handler.

        Args:
            generate_reports_use_case: Use case for report generation
            compare_reports_use_case: Use case for report comparison
            validate_report_use_case: Use case for report input validation
            config: Configuration object
            console: Rich console instance

        """
        self._use_case = generate_reports_use_case
        self._compare_use_case = compare_reports_use_case
        self._config = config
        self._console = console
        self._formatter = ConsoleFormatter(console)
        self._validator = InputValidator(self._formatter, validate_report_use_case)

    def diff_command(
        self,
        *,
        report_a: Annotated[
            Path,
            typer.Option(
                "--report-a",
                help="Path to first pytest-json-report JSON file",
                exists=True,
                file_okay=True,
                dir_okay=False,
            ),
        ],
        report_b: Annotated[
            Path,
            typer.Option(
                "--report-b",
                help="Path to second pytest-json-report JSON file",
                exists=True,
                file_okay=True,
                dir_okay=False,
            ),
        ],
    ) -> None:
        """Compare two pytest JSON reports and summarize differences."""
        try:
            diff = self._compare_use_case.compare(report_a, report_b)
            self._render_diff(diff)
        except ReportingError as e:
            suggestion = f"\n💡 Suggestion: {e.suggestion}" if e.suggestion else ""
            self._formatter.print_error(f"❌ {e}{suggestion}")
            raise typer.Exit(code=1) from e
        except Exception as e:
            self._formatter.print_error(f"❌ Error: {e}")
            raise typer.Exit(code=1) from e

    def generate_command(  # noqa: PLR0913
        self,
        *,
        json_report: Annotated[
            Path,
            typer.Option(
                "--json-report",
                help="Path to pytest-json-report JSON file",
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
        """Generate pytest summary and QA sign-off reports."""
        verbosity = resolve_verbosity(verbose=verbose, quiet=quiet, formatter=self._formatter)
        self._config = apply_profile(profile, self._config, self._formatter)
        options = self._build_report_options(
            json_report=json_report,
            out=out,
            env=env,
            build=build,
            commit=commit,
            target_url=target_url,
            max_failures=max_failures,
            no_llm=no_llm,
            regenerate_narratives=regenerate_narratives,
        )

        # Handle dry-run mode
        if dry_run:
            self._validator.validate_dry_run(
                json_report=options.json_report,
                out=options.out,
                enable_llm=options.enable_llm,
                verbosity=verbosity,
            )
            return

        # Validate inputs and create output directory
        self._validator.validate_inputs(
            json_report=options.json_report,
            out=options.out,
            verbosity=verbosity,
            create_output_dir=True,
        )

        # Generate reports with error handling
        try:
            result = self._generate_reports(
                options=options,
                environment=self._build_environment_meta(options),
                verbosity=verbosity,
            )

            self._formatter.print_generation_results(
                verbosity=verbosity,
                result=result,
            )

        except ReportingError as e:
            suggestion = f"\n💡 Suggestion: {e.suggestion}" if e.suggestion else ""
            self._formatter.print_error(f"❌ {e}{suggestion}")
            raise typer.Exit(code=1) from e
        except Exception as e:
            self._formatter.print_error(f"❌ Error: {e}")
            raise typer.Exit(code=1) from e

    def validate_config_command(
        self,
        *,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable verbose output",
            ),
        ] = False,
    ) -> None:
        """Validate configuration settings."""
        verbosity = OutputVerbosity.VERBOSE if verbose else OutputVerbosity.NORMAL

        try:
            self._formatter.print_info("🔍 [bold]Validating configuration...[/bold]", verbosity)
            self._console.print()
            config = self._config

            config_table = Table(show_header=False, box=None, padding=(0, 2))
            config_table.add_column("Setting", style="cyan", no_wrap=True)
            config_table.add_column("Value", style="white")

            config_table.add_row("Base URL", config.llm_base_url)
            config_table.add_row("Model", config.llm_model)
            config_table.add_row("Timeout", f"{config.llm_timeout}s")

            if verbosity == OutputVerbosity.VERBOSE:
                config_table.add_row("Log Level", config.log_level)
                config_table.add_row("Log Format", config.log_format)
                if config.prompt_template_path:
                    config_table.add_row("Prompt Template", config.prompt_template_path)

            self._render_config_panel(config_table)

        except typer.Exit:
            raise
        except Exception as e:
            self._formatter.print_error(f"❌ Validation failed with error: {e}")
            self._console.print()
            self._formatter.print_info(
                "💡 This might indicate a configuration error. Check your .env file.",
                verbosity,
            )
            raise typer.Exit(code=1) from e
        else:
            self._formatter.print_success("✅ [bold]Configuration is valid.[/bold]", verbosity)
            return

    def _build_report_options(  # noqa: PLR0913
        self,
        *,
        json_report: Path,
        out: Path,
        env: str | None,
        build: str | None,
        commit: str | None,
        target_url: str | None,
        max_failures: int,
        no_llm: bool,
        regenerate_narratives: bool,
    ) -> ReportOptions:
        """Build report options from CLI flags."""
        return ReportOptions(
            json_report=json_report,
            out=out,
            env=env,
            build=build,
            commit=commit,
            target_url=target_url,
            max_failures=None if max_failures == -1 else max_failures,
            enable_llm=not no_llm,
            regenerate_narratives=regenerate_narratives,
        )

    def _build_environment_meta(self, options: ReportOptions) -> EnvironmentMeta:
        """Build environment metadata for report generation."""
        return EnvironmentMeta(
            env=options.env,
            build=options.build,
            commit=options.commit,
            target_url=options.target_url,
        )

    def _render_config_panel(self, config_table: Table) -> None:
        """Render the configuration panel."""
        panel = Panel(config_table, title="📋 Configuration", border_style="blue")
        self._console.print(panel)
        self._console.print()

    def _render_diff(self, diff: ReportDiff) -> None:
        """Render diff results to the console."""
        table = Table(title="Report Diff Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", style="green", justify="right")
        table.add_row("New failures", str(len(diff.new_failures)))
        table.add_row("Fixed tests", str(len(diff.fixed_tests)))
        table.add_row("Regressions", str(len(diff.regressions)))
        self._console.print(table)
        self._console.print()

        self._render_diff_section("Regressions", diff.regressions, "bold red")
        self._render_diff_section("New failures", diff.new_failures, "bold yellow")
        self._render_diff_section("Fixed tests", diff.fixed_tests, "bold green")

    def _render_diff_section(self, title: str, items: list, style: str) -> None:
        """Render diff section with a title and list of identifiers."""
        if not items:
            return

        self._console.print(f"[{style}]{title}:[/{style}]")
        for identifier in items:
            self._console.print(f"- {identifier.suite}::{identifier.name}")
        self._console.print()

    def _generate_reports(
        self,
        *,
        options: ReportOptions,
        environment: EnvironmentMeta,
        verbosity: OutputVerbosity,
    ) -> GenerationResult:
        """Execute report generation with progress tracking.

        Args:
            options: Report generation options
            environment: Environment metadata
            verbosity: Output verbosity level

        Returns:
            Generation result with paths and metrics

        """
        start_time = time.time()
        tracker = ProgressTracker(self._console, verbosity)

        with tracker.track_generation():
            # Stage 1: Preparation
            tracker.update_stage("📊 Preparing input report...", 0)
            tracker.log_verbose(f"Reading: {options.json_report}")
            tracker.log_verbose("Preparation completed")
            tracker.update_stage("📊 Preparing input report...", 1)

            # Stage 2: LLM status check
            tracker.update_stage("🤖 Checking LLM status...", 1)
            llm_status = "enabled" if options.enable_llm else "disabled"
            tracker.log_verbose(f"LLM narrative generation: {llm_status}")
            tracker.update_stage("🤖 Checking LLM status...", 2)

            # Stage 3: Generation
            tracker.update_stage("📝 Generating reports...", 2)
            gen_start = time.time()

            generation_result = self._use_case.generate(
                report_path=options.json_report,
                output_dir=options.out,
                environment=environment,
                max_failures=options.max_failures,
                enable_llm=options.enable_llm,
                regenerate_narratives=options.regenerate_narratives,
            )

            gen_duration = time.time() - gen_start
            tracker.log_verbose(f"Generation completed in {gen_duration:.2f}s")
            tracker.update_stage("📝 Generating reports...", 3)

            # Stage 4: File size calculation
            tracker.update_stage("📏 Calculating file sizes...", 3)
            summary_size = generation_result.summary_path.stat().st_size
            signoff_size = generation_result.signoff_path.stat().st_size
            tracker.update_stage("📏 Calculating file sizes...", 4)

        total_duration = time.time() - start_time
        return GenerationResult(
            summary_path=generation_result.summary_path,
            signoff_path=generation_result.signoff_path,
            summary_size=summary_size,
            signoff_size=signoff_size,
            total_duration=total_duration,
        )
