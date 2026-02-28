"""Unit tests for the k6 CLI adapter."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6SummaryTableResult
from qa_report_generator.domain.exceptions import ReportingError


class StubK6SummaryUseCase:
    """Stub k6 summary table use case."""

    def generate_k6_summary_table(self, *, report_files: list[Path], output_path: Path) -> K6SummaryTableResult:
        """Return a deterministic summary result."""
        return K6SummaryTableResult(output_path=output_path, rows_count=len(report_files))


class SpyExtractionUseCase:
    """Spy extraction use case for command assertions."""

    def __init__(self) -> None:
        """Initialize call storage."""
        self.calls: list[tuple[str, Path, Path]] = []

    def extract(self, *, service: str, report_path: Path, output_path: Path) -> K6ServiceExtractionResult:
        """Record call and return deterministic extraction result."""
        self.calls.append((service, report_path, output_path))
        return K6ServiceExtractionResult(
            output_path=output_path,
            service=service,
            extracted={"service": service},
        )


class FailingExtractionUseCase:
    """Extraction use case stub that raises domain error."""

    def extract(self, *, service: str, report_path: Path, output_path: Path) -> K6ServiceExtractionResult:
        """Raise reporting error."""
        del service, report_path, output_path
        msg = "boom"
        raise ReportingError(msg)


def test_extract_command_uses_default_output_path(tmp_path: Path) -> None:
    """Extract command uses service-specific default output path when omitted."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    extraction_use_case = SpyExtractionUseCase()
    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=extraction_use_case,
    )

    adapter.extract_command(
        service="megatron",
        report=report_path,
        out_file=None,
    )

    assert len(extraction_use_case.calls) == 1
    service, called_report, called_output = extraction_use_case.calls[0]
    assert service == "megatron"
    assert called_report == report_path
    assert called_output == Path("out/k6/extracted_megatron.json")


def test_extract_command_raises_typer_exit_on_reporting_error(tmp_path: Path) -> None:
    """Extract command converts domain reporting errors to Typer exit."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=FailingExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.extract_command(
            service="megatron",
            report=report_path,
            out_file=None,
        )
