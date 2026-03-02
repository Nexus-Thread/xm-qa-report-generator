"""CLI adapter that exposes k6-oriented commands."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from qa_report_generator.application.ports.input import (
    ExtractK6ServiceMetricsUseCase,
    GenerateK6SummaryTableUseCase,
)
from qa_report_generator.domain.exceptions import ReportingError


class K6CliAdapter:
    """CLI adapter that exposes only k6-oriented commands."""

    def __init__(
        self,
        generate_k6_summary_table_use_case: GenerateK6SummaryTableUseCase,
        extract_k6_service_metrics_use_case: ExtractK6ServiceMetricsUseCase,
    ) -> None:
        """Initialize k6-focused CLI adapter."""
        self._console = Console()
        self._k6_summary_table_use_case = generate_k6_summary_table_use_case
        self._extract_k6_service_metrics_use_case = extract_k6_service_metrics_use_case

        self._app = typer.Typer(
            help="Generate consolidated k6 summary tables",
            add_completion=False,
        )

        @self._app.callback()
        def _k6_callback() -> None:
            """Run k6-focused CLI commands."""

        self._app.command(name="generate")(self.generate_command)
        self._app.command(name="extract")(self.extract_command)

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
    ) -> None:
        """Generate and print consolidated k6 summary rows from file(s) or directories."""
        report_files = self._resolve_report_files(report)

        try:
            result = self._k6_summary_table_use_case.generate_k6_summary_table(report_files=report_files)
        except ReportingError as e:
            suggestion = f"\n💡 Suggestion: {e.suggestion}" if e.suggestion else ""
            self._console.print(f"[red]❌ {e}{suggestion}[/red]")
            raise typer.Exit(code=1) from e
        except Exception as e:
            self._console.print(f"[red]❌ Error: {e}[/red]")
            raise typer.Exit(code=1) from e
        else:
            rows_payload = [asdict(row) for row in result.rows]
            self._console.print("[green]✅ Parsed k6 summary rows[/green]")
            self._console.print_json(json.dumps(rows_payload, ensure_ascii=False, indent=2, sort_keys=True))

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

    def extract_command(
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
            Path,
            typer.Option(
                "--report",
                help="Input k6 JSON file",
                exists=True,
                file_okay=True,
                dir_okay=False,
            ),
        ],
    ) -> None:
        """Extract and print service-specific deterministic metrics from one k6 JSON report."""
        try:
            result = self._extract_k6_service_metrics_use_case.extract(
                service=service,
                report_path=report,
            )
        except ReportingError as e:
            suggestion = f"\n💡 Suggestion: {e.suggestion}" if e.suggestion else ""
            self._console.print(f"[red]❌ {e}{suggestion}[/red]")
            raise typer.Exit(code=1) from e
        except Exception as e:
            self._console.print(f"[red]❌ Error: {e}[/red]")
            raise typer.Exit(code=1) from e
        else:
            self._console.print("[green]✅ Parsed extracted model[/green]")
            self._console.print(f"[dim]Service: {result.service}[/dim]")
            self._console.print_json(json.dumps(result.extracted, ensure_ascii=False, indent=2, sort_keys=True))

    def run(self) -> None:
        """Run the CLI application."""
        self._app()
