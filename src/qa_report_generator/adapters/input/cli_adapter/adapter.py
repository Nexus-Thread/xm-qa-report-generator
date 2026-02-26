"""CLI adapter for report generation commands."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from qa_report_generator.adapters.input.cli_adapter.commands import CommandHandler
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.application.ports.input import (
    CompareReportsUseCase,
    GenerateK6SummaryTableUseCase,
    GenerateReportsUseCase,
    ValidateReportUseCase,
)
from qa_report_generator.domain.exceptions import ReportingError


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
        generate_k6_summary_table_use_case: GenerateK6SummaryTableUseCase,
    ) -> None:
        """Initialize k6-focused CLI adapter."""
        self._console = Console()
        self._k6_summary_table_use_case = generate_k6_summary_table_use_case

        self._app = typer.Typer(
            help="Generate consolidated k6 summary tables",
            add_completion=False,
        )

        @self._app.callback()
        def _k6_callback() -> None:
            """Run k6-focused CLI commands."""

        self._app.command(name="generate")(self.generate_command)

    def generate_command(
        self,
        *,
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
        out_file: Annotated[
            Path,
            typer.Option(
                "--out-file",
                help="Output markdown file for consolidated summary table",
            ),
        ] = Path("out/k6/performance_summary.md"),
    ) -> None:
        """Generate consolidated k6 summary table from file(s) or directories."""
        report_files = self._resolve_report_files(report)

        try:
            result = self._k6_summary_table_use_case.generate_k6_summary_table(
                report_files=report_files,
                output_path=out_file,
            )
        except ReportingError as e:
            suggestion = f"\n💡 Suggestion: {e.suggestion}" if e.suggestion else ""
            self._console.print(f"[red]❌ {e}{suggestion}[/red]")
            raise typer.Exit(code=1) from e
        except Exception as e:
            self._console.print(f"[red]❌ Error: {e}[/red]")
            raise typer.Exit(code=1) from e
        else:
            self._console.print(f"[green]✅ K6 summary table: {result.output_path}[/green]")
            self._console.print(f"[dim]Rows: {result.rows_count}[/dim]")

    def _resolve_report_files(self, report_inputs: list[Path]) -> list[Path]:
        """Resolve report inputs into a de-duplicated file list."""
        resolved: list[Path] = []

        for report_input in report_inputs:
            if report_input.is_dir():
                dir_files = sorted(path for path in report_input.glob("*.json") if path.is_file())
                if not dir_files:
                    self._console.print(f"[red]❌ No JSON report files found in directory: {report_input}[/red]")
                    raise typer.Exit(code=1)
                resolved.extend(dir_files)
                continue

            if report_input.is_file():
                if report_input.suffix.lower() != ".json":
                    self._console.print(f"[red]❌ Report file must be a JSON file: {report_input}[/red]")
                    raise typer.Exit(code=1)
                resolved.append(report_input)
                continue

            self._console.print(f"[red]❌ Invalid report input: {report_input}[/red]")
            raise typer.Exit(code=1)

        return sorted(set(resolved))

    def run(self) -> None:
        """Run the CLI application."""
        self._app()
