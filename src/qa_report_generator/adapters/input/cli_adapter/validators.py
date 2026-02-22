"""Input validation logic for CLI adapter."""

import tempfile
from pathlib import Path

import typer

from qa_report_generator.adapters.input.cli_adapter.formatters import ConsoleFormatter
from qa_report_generator.adapters.input.cli_adapter.types import OutputVerbosity
from qa_report_generator.application.ports.input import ValidateReportUseCase
from qa_report_generator.domain.exceptions import ReportingError


class InputValidator:
    """Validates CLI inputs before processing."""

    def __init__(self, formatter: ConsoleFormatter, validate_report_use_case: ValidateReportUseCase) -> None:
        """Initialize validator with a console formatter."""
        self._formatter = formatter
        self._validate_report_use_case = validate_report_use_case

    def validate_inputs(
        self,
        *,
        json_report: Path,
        out: Path,
        verbosity: OutputVerbosity,
        create_output_dir: bool,
    ) -> int:
        """Validate input report path and output directory.

        Returns:
            Input file size in bytes

        Raises:
            typer.Exit: If validation fails

        """
        self._formatter.print_verbose(f"  Checking input file: {json_report}", verbosity)

        if not json_report.exists():
            self._formatter.print_error(f"❌ Input file does not exist: {json_report}")
            raise typer.Exit(code=1)

        if not json_report.is_file():
            self._formatter.print_error(f"❌ Input path is not a file: {json_report}")
            raise typer.Exit(code=1)

        input_size = json_report.stat().st_size
        self._formatter.print_success(
            f"✅ Input file exists ({self._formatter.format_file_size(input_size)})",
            verbosity,
        )

        self._formatter.print_verbose(f"  Checking output directory: {out}", verbosity)

        if out.exists() and not out.is_dir():
            self._formatter.print_error(f"❌ Output path exists but is not a directory: {out}")
            raise typer.Exit(code=1)

        output_dir_created = False
        if not out.exists():
            if create_output_dir:
                out.mkdir(parents=True, exist_ok=True)
                output_dir_created = True
                self._formatter.print_success(f"✅ Created output directory: {out}", verbosity)
            else:
                self._formatter.print_info(f"Output directory will be created: {out}", verbosity)

        if out.exists():
            self._ensure_directory_writable(out)
            if not output_dir_created:
                self._formatter.print_success("✅ Output directory exists and is writable", verbosity)

        return input_size

    def validate_dry_run(
        self,
        *,
        json_report: Path,
        out: Path,
        enable_llm: bool,
        verbosity: OutputVerbosity,
    ) -> None:
        """Perform dry-run validation without generating reports.

        Raises:
            typer.Exit: If validation fails

        """
        self._formatter.print_info(
            "🔍 [bold]Dry-run mode:[/bold] Validating inputs without generating reports...",
            verbosity,
        )
        self._formatter.print_blank_line(verbosity)

        self.validate_inputs(
            json_report=json_report,
            out=out,
            verbosity=verbosity,
            create_output_dir=False,
        )

        # Validate JSON structure by parsing
        self._formatter.print_verbose("  Parsing JSON structure...", verbosity)
        try:
            metrics = self._validate_report_use_case.validate_report(json_report)
            self._formatter.print_success(
                f"✅ JSON structure is valid (found {metrics.total} test cases)",
                verbosity,
            )
            self._formatter.print_verbose(
                f"    Passed: {metrics.passed}, Failed: {metrics.failed}, Skipped: {metrics.skipped}",
                verbosity,
            )
        except ReportingError as e:
            self._formatter.print_error(f"❌ Failed to parse JSON ({e.error_code}): {e}")
            raise typer.Exit(code=1) from e
        except Exception as e:
            self._formatter.print_error(f"❌ Failed to parse JSON: {e}")
            raise typer.Exit(code=1) from e

        if enable_llm:
            self._formatter.print_verbose("  LLM narrative generation enabled", verbosity)
        else:
            self._formatter.print_info("LLM disabled (--no-llm)", verbosity)

        # Summary
        self._formatter.print_blank_line(verbosity)
        self._formatter.print_success("🎉 [bold]Dry-run validation passed![/bold]", verbosity)
        self._formatter.print_info(
            "   All inputs are valid and reports would be generated successfully.",
            verbosity,
        )
        self._formatter.print_blank_line(verbosity)
        self._formatter.print_verbose("  Would generate:", verbosity)
        self._formatter.print_verbose(f"    - {out / 'pytest_summary.md'}", verbosity)
        self._formatter.print_verbose(f"    - {out / 'signoff_report.md'}", verbosity)

    def _ensure_directory_writable(self, path: Path) -> None:
        """Ensure directory is writable by creating a temporary file."""
        try:
            with tempfile.NamedTemporaryFile(dir=path):
                return
        except OSError as e:
            self._formatter.print_error(f"❌ Output directory is not writable: {path}")
            raise typer.Exit(code=1) from e
