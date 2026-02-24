"""Input ports for application use cases."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from qa_report_generator.domain.analytics.models import ReportDiff
from qa_report_generator.domain.models import EnvironmentMeta, RunMetrics


@dataclass(frozen=True)
class ReportGenerationResult:
    """Report output paths and timing metrics."""

    summary_path: Path
    signoff_path: Path
    parse_duration: float
    write_duration: float
    total_duration: float


class GenerateReportsUseCase(ABC):
    """Report generation use case interface."""

    @abstractmethod
    def generate(  # noqa: PLR0913
        self,
        report_path: Path,
        output_dir: Path,
        environment: EnvironmentMeta,
        report_format: str,
        max_failures: int | None = 20,
        enable_llm: bool = True,
        regenerate_narratives: bool = False,
    ) -> ReportGenerationResult:
        """Generate test reports from an input file."""


class CompareReportsUseCase(ABC):
    """Report comparison use case interface."""

    @abstractmethod
    def compare(self, report_a: Path, report_b: Path, report_format: str) -> ReportDiff:
        """Compare two test reports and return diff summary."""


class ValidateReportUseCase(ABC):
    """Validate a report input and return parsed metrics."""

    @abstractmethod
    def validate_report(self, report_path: Path, report_format: str) -> RunMetrics:
        """Validate report structure by parsing it."""
