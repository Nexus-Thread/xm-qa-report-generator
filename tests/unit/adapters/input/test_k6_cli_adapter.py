"""Unit tests for the k6 CLI adapter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
)
from qa_report_generator.domain.analytics import (
    K6OverallExecutiveSummary,
    K6ScenarioExecutiveSummary,
    K6ThresholdSummary,
)
from qa_report_generator.domain.exceptions import ReportingError


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
            runs=[
                K6ServiceExtractionRun(
                    source_report_files=[path.name for path in report_paths],
                    extracted={
                        "service": service,
                        "scenario": {"name": "grouped-scenario"},
                        "threshold_results": [
                            {
                                "metric_key": "checks",
                                "expression": "rate>0.99",
                                "status": "pass",
                            }
                        ],
                    },
                )
            ],
            overall_summary=K6OverallExecutiveSummary(
                status="pass",
                total_scenarios=1,
                passed_scenarios=1,
                failed_scenarios=0,
                unknown_scenarios=0,
                scenarios_requiring_attention=[],
                executive_summary="All 1 scenarios passed their evaluated thresholds.",
            ),
            scenario_summaries=[
                K6ScenarioExecutiveSummary(
                    scenario_name="grouped-scenario",
                    env_name=None,
                    source_report_files=[path.name for path in report_paths],
                    status="pass",
                    executor=None,
                    rate=None,
                    duration=None,
                    pre_allocated_vus=None,
                    max_vus=None,
                    threshold_results=[
                        K6ThresholdSummary(
                            metric_key="checks",
                            expression="rate>0.99",
                            status="pass",
                        )
                    ],
                    executive_note="Scenario grouped-scenario met all evaluated thresholds.",
                )
            ],
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


class SpyDebugJsonWriter:
    """Spy writer for persisted model JSON payloads."""

    def __init__(self) -> None:
        """Store persisted debug calls."""
        self.calls: list[tuple[str, object]] = []

    def write_json(self, *, label: str, payload: object) -> Path:
        """Record one debug JSON write call."""
        self.calls.append((label, payload))
        return Path(f"out/test-debug/{label}.json")


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
    assert '"overall_summary"' in captured.out
    assert '"scenario_summaries"' in captured.out
    assert '"executive_note": "Scenario grouped-scenario met all evaluated thresholds."' in captured.out
    assert '"runs"' not in captured.out


def test_generate_command_prints_full_output_when_requested(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Generate command includes detailed runs when full output is requested."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    adapter.generate_command(service="megatron", report=[report_path], output="full")

    captured = capsys.readouterr()
    assert '"runs"' in captured.out
    assert '"source_report_files": [' in captured.out
    assert '"name": "grouped-scenario"' in captured.out


def test_generate_command_writes_model_debug_payload_when_enabled(tmp_path: Path) -> None:
    """Generate command persists final model JSON when configured."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    debug_writer = SpyDebugJsonWriter()

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
        model_debug_json_writer=debug_writer,
        model_debug_json_enabled=True,
    )

    adapter.generate_command(service="megatron", report=[report_path])

    assert debug_writer.calls == []


def test_generate_command_writes_full_output_debug_payload_when_enabled(tmp_path: Path) -> None:
    """Generate command persists the final full output payload when requested."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    debug_writer = SpyDebugJsonWriter()

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
        model_debug_json_writer=debug_writer,
        model_debug_json_enabled=True,
    )

    adapter.generate_command(service="megatron", report=[report_path], output="full")

    assert len(debug_writer.calls) == 1
    label, payload = debug_writer.calls[0]
    assert label == "full_output"
    payload_dict = json.loads(json.dumps(payload))
    assert payload_dict["service"] == "megatron"
    assert "runs" in payload_dict


def test_generate_command_raises_typer_exit_on_empty_service(tmp_path: Path) -> None:
    """Generate command rejects empty service identifier."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter = K6CliAdapter(
        extract_k6_service_metrics_use_case=SpyExtractionUseCase(),
    )

    with pytest.raises(typer.Exit):
        adapter.generate_command(service="   ", report=[report_path])


def test_generate_command_expands_directory_reports_in_sorted_order(tmp_path: Path) -> None:
    """Generate command expands a directory into sorted JSON report paths."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    later_report = reports_dir / "z-report.json"
    earlier_report = reports_dir / "a-report.json"
    ignored_file = reports_dir / "notes.txt"
    later_report.write_text("{}", encoding="utf-8")
    earlier_report.write_text("{}", encoding="utf-8")
    ignored_file.write_text("ignore", encoding="utf-8")

    extraction_use_case = SpyExtractionUseCase()
    adapter = K6CliAdapter(extract_k6_service_metrics_use_case=extraction_use_case)

    adapter.generate_command(service="megatron", report=[reports_dir])

    assert extraction_use_case.calls == [
        ("megatron", [earlier_report, later_report]),
    ]


def test_generate_command_deduplicates_report_files_from_mixed_inputs(tmp_path: Path) -> None:
    """Generate command de-duplicates report files gathered from file and directory inputs."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report_path = reports_dir / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    extraction_use_case = SpyExtractionUseCase()
    adapter = K6CliAdapter(extract_k6_service_metrics_use_case=extraction_use_case)

    adapter.generate_command(service="megatron", report=[report_path, reports_dir])

    assert extraction_use_case.calls == [
        ("megatron", [report_path]),
    ]


def test_generate_command_raises_typer_exit_for_empty_report_directory(tmp_path: Path) -> None:
    """Generate command rejects directories without JSON report files."""
    empty_reports_dir = tmp_path / "empty-reports"
    empty_reports_dir.mkdir()

    adapter = K6CliAdapter(extract_k6_service_metrics_use_case=SpyExtractionUseCase())

    with pytest.raises(typer.Exit):
        adapter.generate_command(service="megatron", report=[empty_reports_dir])


def test_generate_command_raises_typer_exit_when_report_list_is_empty() -> None:
    """Generate command rejects missing report inputs."""
    adapter = K6CliAdapter(extract_k6_service_metrics_use_case=SpyExtractionUseCase())

    with pytest.raises(typer.Exit):
        adapter.generate_command(service="megatron", report=[])
