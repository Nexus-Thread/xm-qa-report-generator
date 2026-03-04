"""Unit tests for the k6 CLI adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import typer

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
    K6ServiceReportResult,
    K6SummaryRow,
    K6SummaryTableResult,
)
from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario
from qa_report_generator.domain.exceptions import ReportingError

if TYPE_CHECKING:
    from pathlib import Path


class StubK6SummaryUseCase:
    """Stub k6 summary table use case."""

    def __init__(self) -> None:
        """Initialize call storage."""
        self.calls: list[list[Path]] = []

    def generate_k6_summary_table(self, *, report_files: list[Path]) -> K6SummaryTableResult:
        """Return a deterministic summary result."""
        self.calls.append(report_files)
        rows = [
            K6SummaryRow(
                report_file=path.name,
                scenario="sample",
                request_rate=1.0,
                iterations=1,
                p95_duration_ms=1.0,
                p99_duration_ms=1.0,
                checks_rate=1.0,
            )
            for path in report_files
        ]
        return K6SummaryTableResult(rows=rows)


class FailingSummaryUseCase:
    """Summary table use case stub that raises domain error."""

    def __init__(self, *, suggestion: str | None = None) -> None:
        """Store optional error suggestion."""
        self._suggestion = suggestion

    def generate_k6_summary_table(self, *, report_files: list[Path]) -> K6SummaryTableResult:
        """Raise reporting error."""
        del report_files
        msg = "boom"
        raise ReportingError(msg, suggestion=self._suggestion)


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


class SpyServiceReportUseCase:
    """Spy service report use case for command assertions."""

    def __init__(self) -> None:
        """Initialize call storage."""
        self.calls: list[tuple[str, list[Path]]] = []

    def generate_service_report(self, *, service: str, report_paths: list[Path]) -> K6ServiceReportResult:
        """Record call and return deterministic service report payload."""
        self.calls.append((service, report_paths))
        parsed_report = K6ParsedReport(
            service=service,
            scenarios=[
                K6Scenario(
                    source_report_file=report_paths[0].name,
                    name="sample",
                    env_name="staging",
                    executor="constant-arrival-rate",
                    rate=1.0,
                    duration="1m",
                    pre_allocated_vus=1,
                    max_vus=2,
                    test_run_duration_ms=60_000,
                    thresholds={},
                    metrics={},
                    raw_payload={},
                )
            ],
        )
        extraction = K6ServiceExtractionResult(
            service=service,
            extracted_runs=[K6ServiceExtractionRun(report_file=path.name, extracted={"service": service}) for path in report_paths],
        )
        return K6ServiceReportResult(
            service=service,
            parsed_report=parsed_report,
            extraction=extraction,
        )


def test_extract_command_passes_service_and_report_to_use_case(tmp_path: Path) -> None:
    """Extract command forwards service and resolved report paths to use case."""
    report_path_1 = tmp_path / "report-1.json"
    report_path_2 = tmp_path / "report-2.json"
    report_path_1.write_text("{}", encoding="utf-8")
    report_path_2.write_text("{}", encoding="utf-8")

    extraction_use_case = SpyExtractionUseCase()
    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=extraction_use_case,
    )

    adapter.extract_command(service="  megatron  ", report=[report_path_1, report_path_2])

    assert len(extraction_use_case.calls) == 1
    service, called_reports = extraction_use_case.calls[0]
    assert service == "megatron"
    assert called_reports == [report_path_1, report_path_2]


def test_generate_command_resolves_directory_reports_and_deduplicates(tmp_path: Path) -> None:
    """Generate command forwards sorted unique JSON reports to use case."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report_path_1 = reports_dir / "a.json"
    report_path_2 = reports_dir / "b.json"
    report_path_1.write_text("{}", encoding="utf-8")
    report_path_2.write_text("{}", encoding="utf-8")
    (reports_dir / "skip.txt").write_text("ignored", encoding="utf-8")

    summary_use_case = StubK6SummaryUseCase()
    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=summary_use_case,
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    adapter.generate_command(report=[reports_dir, report_path_2])

    assert len(summary_use_case.calls) == 1
    assert summary_use_case.calls[0] == [report_path_1, report_path_2]


def test_generate_command_raises_typer_exit_on_reporting_error(tmp_path: Path) -> None:
    """Generate command converts domain reporting errors to Typer exit."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=FailingSummaryUseCase(),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.generate_command(report=[report_path])


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
            report=[report_path],
        )


def test_extract_command_raises_typer_exit_on_non_json_report(tmp_path: Path) -> None:
    """Extract command rejects non-JSON report files."""
    report_path = tmp_path / "report.txt"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.extract_command(
            service="megatron",
            report=[report_path],
        )


def test_generate_command_prints_success_message_and_json_payload(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Generate command prints success text and JSON payload."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    adapter.generate_command(report=[report_path])

    captured = capsys.readouterr()
    assert "✅ Parsed k6 summary rows" in captured.out
    assert '"report_file": "report.json"' in captured.out
    assert '"scenario": "sample"' in captured.out


def test_extract_command_prints_success_message_heading_and_json_payload(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Extract command prints success text, heading, and JSON payload."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    adapter.extract_command(service="megatron", report=[report_path])

    captured = capsys.readouterr()
    assert "✅ Extracted service metrics" in captured.out
    assert "Service: megatron" in captured.out
    assert '"service": "megatron"' in captured.out
    assert '"report_file": "report.json"' in captured.out


def test_extract_command_raises_typer_exit_on_empty_service(tmp_path: Path) -> None:
    """Extract command rejects empty service identifier."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.extract_command(service="   ", report=[report_path])


def test_report_command_passes_service_and_report_to_use_case(tmp_path: Path) -> None:
    """Report command forwards service and report paths to service report use case."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    service_report_use_case = SpyServiceReportUseCase()
    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
        generate_k6_service_report_use_case=service_report_use_case,
    )

    adapter.report_command(service="megatron", report=[report_path])

    assert service_report_use_case.calls == [("megatron", [report_path])]


def test_report_command_raises_typer_exit_when_use_case_not_configured(tmp_path: Path) -> None:
    """Report command fails fast when service report use case is missing."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.report_command(service="megatron", report=[report_path])


def test_report_command_prints_success_message_heading_and_json_payload(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Report command prints success text, heading, and combined JSON payload."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=StubK6SummaryUseCase(),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
        generate_k6_service_report_use_case=SpyServiceReportUseCase(),
    )

    adapter.report_command(service="megatron", report=[report_path])

    captured = capsys.readouterr()
    assert "✅ Generated service report" in captured.out
    assert "Service: megatron" in captured.out
    assert '"parsed_report"' in captured.out
    assert '"extraction"' in captured.out


def test_generate_command_raises_typer_exit_and_prints_reporting_suggestion(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Generate command prints reporting suggestion when provided."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        generate_k6_summary_table_use_case=FailingSummaryUseCase(suggestion="Check your report format"),
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.generate_command(report=[report_path])

    captured = capsys.readouterr()
    assert "❌ boom" in captured.out
    assert "💡 Suggestion: Check your report format" in captured.out
