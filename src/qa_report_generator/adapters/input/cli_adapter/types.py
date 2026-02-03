"""Type definitions for CLI adapter."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


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


@dataclass(frozen=True)
class GenerationResult:
    """Generated report outputs and metrics."""

    summary_path: Path
    signoff_path: Path
    summary_size: int
    signoff_size: int
    total_duration: float


class OutputVerbosity(str, Enum):
    """Output verbosity levels for CLI."""

    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"
