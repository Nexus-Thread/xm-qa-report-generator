"""Input port protocols for application use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.dtos import (
        GeneratedReportsResult,
        K6ServiceExtractionResult,
        K6ServiceReportResult,
        K6SummaryTableResult,
        ReportValidationMetrics,
    )
    from qa_report_generator.domain.analytics.models import ReportDiff
    from qa_report_generator.domain.models import EnvironmentMeta


class GenerateReportsUseCase(Protocol):
    """Port for generating human-readable reports from a JSON report."""

    def generate(  # noqa: PLR0913
        self,
        *,
        report_path: Path,
        output_dir: Path,
        environment: EnvironmentMeta,
        report_format: str,
        max_failures: int | None,
        enable_llm: bool,
        regenerate_narratives: bool,
    ) -> GeneratedReportsResult:
        """Generate report artifacts."""


class GenerateK6SummaryTableUseCase(Protocol):
    """Port for parsing k6 reports into summary rows."""

    def generate_k6_summary_table(self, *, report_files: list[Path]) -> K6SummaryTableResult:
        """Return parsed summary rows."""


class ExtractK6ServiceMetricsUseCase(Protocol):
    """Port for deterministic service-specific k6 metric extraction."""

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Extract service-specific structured metrics."""


class GenerateK6ServiceReportUseCase(Protocol):
    """Port for generating parsed and extracted service report payloads."""

    def generate_service_report(self, *, service: str, report_paths: list[Path]) -> K6ServiceReportResult:
        """Generate service report payload using parsed and extracted data."""


class CompareReportsUseCase(Protocol):
    """Port for diffing two reports."""

    def compare(self, report_a: Path, report_b: Path, *, report_format: str) -> ReportDiff:
        """Return report diff."""


class ValidateReportUseCase(Protocol):
    """Port for validating incoming report structure."""

    def validate_report(self, report_path: Path, report_format: str) -> ReportValidationMetrics:
        """Validate report and return summary metrics."""
