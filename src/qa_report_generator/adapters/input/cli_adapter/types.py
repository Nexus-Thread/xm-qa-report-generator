"""Type definitions for CLI adapter."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ReportFormat(StrEnum):
    """Supported input report formats."""

    PYTEST = "pytest"
    K6 = "k6"


@dataclass(frozen=True)
class ReportOptions:
    """Options for report generation."""

    json_report: Path
    out: Path
    env: str | None
    build: str | None
    commit: str | None
    target_url: str | None
    max_failures: int | None
    enable_llm: bool
    regenerate_narratives: bool
    report_format: str


@dataclass(frozen=True)
class GenerationResult:
    """Generated report outputs and metrics."""

    summary_path: Path
    signoff_path: Path
    summary_size: int
    signoff_size: int
    total_duration: float


class OutputVerbosity(StrEnum):
    """Output verbosity levels for CLI."""

    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"
