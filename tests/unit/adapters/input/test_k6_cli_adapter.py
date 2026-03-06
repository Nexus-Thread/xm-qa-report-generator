"""Unit tests for the k6 CLI adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import typer

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
)
from qa_report_generator.domain.exceptions import ReportingError

if TYPE_CHECKING:
    from pathlib import Path


class SpyExtractionUseCase:
    """Spy extraction use case for command assertions."""

    def __init__(self) -> None:
        """Initialize call storage."""
        self.calls: list[tuple[str, list[Path]]] = []

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Record call and return deterministic extraction result."""
        self.calls.append((service, report_paths))
        return K6ServiceExtractionResult(
            service=service,
            mode="service_specific",
            extracted_runs=[K6ServiceExtractionRun(report_file=path.name, extracted={"service": service}) for path in report_paths],
        )


class FailingExtractionUseCase:
    """Extraction use case stub that raises domain error."""

    def __init__(self, *, suggestion: str | None = None) -> None:
        """Store optional error suggestion."""
        self._suggestion = suggestion

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Raise reporting error."""
        del service, report_paths
        msg = "boom"
        raise ReportingError(msg, suggestion=self._suggestion)


class CrashingExtractionUseCase:
    """Extraction use case stub that raises an unexpected error."""

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Raise unexpected runtime error."""
        del service, report_paths
        msg = "unexpected boom"
        raise RuntimeError(msg)


def test_generate_command_passes_service_and_report_to_use_case(tmp_path: Path) -> None:
    """Generate command forwards service and resolved report paths to use case."""
    report_path_1 = tmp_path / "report-1.json"
    report_path_2 = tmp_path / "report-2.json"
    report_path_1.write_text("{}", encoding="utf-8")
    report_path_2.write_text("{}", encoding="utf-8")

    extraction_use_case = SpyExtractionUseCase()
    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=extraction_use_case,
    )

    adapter.generate_command(service="  megatron  ", report=[report_path_1, report_path_2])

    assert len(extraction_use_case.calls) == 1
    service, called_reports = extraction_use_case.calls[0]
    assert service == "megatron"
    assert called_reports == [report_path_1, report_path_2]


def test_generate_command_raises_typer_exit_on_reporting_error(tmp_path: Path) -> None:
    """Generate command converts domain reporting errors to Typer exit."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=FailingExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.generate_command(
            service="megatron",
            report=[report_path],
        )


def test_generate_command_propagates_unexpected_errors(tmp_path: Path) -> None:
    """Generate command propagates unexpected errors without wrapping them."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=CrashingExtractionUseCase(),
    )

    with pytest.raises(RuntimeError, match="unexpected boom"):
        adapter.generate_command(
            service="megatron",
            report=[report_path],
        )


def test_generate_command_raises_typer_exit_on_non_json_report(tmp_path: Path) -> None:
    """Generate command rejects non-JSON report files."""
    report_path = tmp_path / "report.txt"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.generate_command(
            service="megatron",
            report=[report_path],
        )


def test_generate_command_prints_success_message_heading_and_json_payload(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Generate command prints success text, heading, and JSON payload."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    adapter.generate_command(service="megatron", report=[report_path])

    captured = capsys.readouterr()
    assert "✅ Generated service metrics" in captured.out
    assert "Service: megatron" in captured.out
    assert '"mode": "service_specific"' in captured.out
    assert '"service": "megatron"' in captured.out
    assert '"report_file": "report.json"' in captured.out


def test_generate_command_raises_typer_exit_on_empty_service(tmp_path: Path) -> None:
    """Generate command rejects empty service identifier."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.generate_command(service="   ", report=[report_path])
