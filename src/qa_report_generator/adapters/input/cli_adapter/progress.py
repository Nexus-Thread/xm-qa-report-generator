"""Progress tracking utilities for CLI commands."""

from collections.abc import Generator
from contextlib import contextmanager

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from qa_report_generator.adapters.input.cli_adapter.types import OutputVerbosity


class ProgressTracker:
    """Tracks and displays progress for report generation."""

    def __init__(self, console: Console, verbosity: OutputVerbosity) -> None:
        """Initialize progress tracker.

        Args:
            console: Rich console for output
            verbosity: Output verbosity level

        """
        self._console = console
        self._verbosity = verbosity
        self._disabled = verbosity == OutputVerbosity.QUIET
        self._progress: Progress | None = None
        self._task_id: TaskID | None = None

    @contextmanager
    def track_generation(self) -> Generator[None, None, None]:
        """Context manager for tracking report generation progress."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self._console,
            disable=self._disabled,
        ) as progress:
            self._progress = progress
            self._task_id = progress.add_task("Generating reports...", total=4)
            yield

    def update_stage(self, stage: str, step: int) -> None:
        """Update progress to a new stage.

        Args:
            stage: Description of the current stage
            step: Step number (0-4)

        """
        if not self._disabled:
            progress, task_id = self._get_progress_context()
            progress.update(task_id, description=stage, completed=step)

    def log_verbose(self, message: str) -> None:
        """Log a verbose message during progress tracking.

        Args:
            message: Message to log

        """
        if self._verbosity == OutputVerbosity.VERBOSE:
            self._console.print(f"[dim]{message}[/dim]")

    def _get_progress_context(self) -> tuple[Progress, TaskID]:
        """Get active progress context for updates."""
        if self._progress is None or self._task_id is None:
            msg = "Progress tracking has not been initialized"
            raise RuntimeError(msg)
        return self._progress, self._task_id
