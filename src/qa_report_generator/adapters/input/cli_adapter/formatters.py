"""Console output formatters for CLI adapter."""

from rich.console import Console

from qa_report_generator.adapters.input.cli_adapter.types import (
    GenerationResult,
    OutputVerbosity,
)

# File size formatting constants
FILE_SIZE_UNITS = ("B", "KB", "MB", "GB")
FILE_SIZE_BASE = 1024.0


class ConsoleFormatter:
    """Formats console output for CLI commands."""

    def __init__(self, console: Console) -> None:
        """Initialize formatter with a console instance."""
        self._console = console

    def print_info(self, message: str, verbosity: OutputVerbosity) -> None:
        """Print info message if verbosity allows."""
        if verbosity != OutputVerbosity.QUIET:
            self._console.print(f"[blue]{message}[/blue]")

    def print_success(self, message: str, verbosity: OutputVerbosity) -> None:
        """Print success message if verbosity allows."""
        if verbosity != OutputVerbosity.QUIET:
            self._console.print(f"[green]{message}[/green]")

    def print_verbose(self, message: str, verbosity: OutputVerbosity) -> None:
        """Print verbose message if verbosity is verbose."""
        if verbosity == OutputVerbosity.VERBOSE:
            self._console.print(f"[dim]{message}[/dim]")

    def print_error(self, message: str) -> None:
        """Print error message (always shown)."""
        error_console = Console(stderr=True)
        error_console.print(f"[red]{message}[/red]")

    def print_blank_line(self, verbosity: OutputVerbosity) -> None:
        """Print a blank line if verbosity allows."""
        if verbosity != OutputVerbosity.QUIET:
            self._console.print()

    def format_file_size(self, size_bytes: float) -> str:
        """Format file size in human-readable format."""
        for unit in FILE_SIZE_UNITS:
            if size_bytes < FILE_SIZE_BASE:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= FILE_SIZE_BASE
        return f"{size_bytes:.1f} TB"

    def print_generation_results(
        self,
        *,
        verbosity: OutputVerbosity,
        result: GenerationResult,
    ) -> None:
        """Print formatted generation results."""
        from rich.table import Table

        if verbosity != OutputVerbosity.QUIET:
            self._console.print()

        if verbosity == OutputVerbosity.VERBOSE:
            table = Table(title="Generated Reports", show_header=True, header_style="bold magenta")
            table.add_column("Report Type", style="cyan", width=20)
            table.add_column("Path", style="white")
            table.add_column("Size", style="green", justify="right", width=12)

            table.add_row(
                "Summary Report",
                str(result.summary_path),
                self.format_file_size(result.summary_size),
            )
            table.add_row(
                "Sign-off Report",
                str(result.signoff_path),
                self.format_file_size(result.signoff_size),
            )

            self._console.print(table)
            self._console.print()
            self.print_verbose(f"Total generation time: {result.total_duration:.2f}s", verbosity)
        else:
            self.print_success(f"✅ Summary report: {result.summary_path}", verbosity)
            if verbosity != OutputVerbosity.QUIET:
                self._console.print(f"   [dim]({self.format_file_size(result.summary_size)})[/dim]")

            self.print_success(f"✅ Sign-off report: {result.signoff_path}", verbosity)
            if verbosity != OutputVerbosity.QUIET:
                self._console.print(f"   [dim]({self.format_file_size(result.signoff_size)})[/dim]")

        if verbosity != OutputVerbosity.QUIET:
            self._console.print()
            self.print_success("🎉 [bold]Reports generated successfully![/bold]", verbosity)
