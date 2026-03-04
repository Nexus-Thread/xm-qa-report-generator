"""Input port protocols for application use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.dtos import (
        K6ServiceExtractionResult,
        K6ServiceReportResult,
        K6SummaryTableResult,
    )


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
