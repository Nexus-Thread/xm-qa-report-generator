"""Unit tests for application use cases."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from qa_report_generator.application.dtos import ParsedReport
from qa_report_generator.application.use_cases import (
    K6SummaryTableService,
    ReportComparisonService,
    ReportGenerationService,
    ReportValidationService,
)
from qa_report_generator.domain.exceptions import ConfigurationError, ReportingError
from qa_report_generator.domain.models import EnvironmentMeta, RunMetrics
from qa_report_generator.domain.value_objects import Duration


def _make_metrics() -> RunMetrics:
    return RunMetrics(
        total=1,
        passed=1,
        failed=0,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=[],
    )


def _make_parsed_report() -> ParsedReport:
    return ParsedReport(metrics=_make_metrics())


def _make_parsers() -> dict[str, Any]:
    parser = Mock()
    parser.parse.return_value = _make_parsed_report()
    return {"pytest": parser}


def test_report_generation_logs_timings(caplog: Any) -> None:
    """Ensure timing summary log is emitted on report generation."""
    parsers = _make_parsers()
    writer = Mock()
    writer.save_reports.return_value = (Path("summary.md"), Path("signoff.md"))
    narrative = Mock()

    service = ReportGenerationService(parsers, writer, narrative)

    with caplog.at_level("INFO"):
        service.generate(
            report_path=Path("report.json"),
            output_dir=Path("out"),
            environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
            report_format="pytest",
            enable_llm=True,
        )

    assert any("Report generated in" in record.message and record.levelname == "INFO" for record in caplog.records)


def test_report_generation_uses_failure_clustering_threshold() -> None:
    """Use the configured failure clustering threshold."""
    parsers = _make_parsers()
    writer = Mock()
    writer.save_reports.return_value = (Path("summary.md"), Path("signoff.md"))
    narrative = Mock()

    service = ReportGenerationService(
        parsers,
        writer,
        narrative,
        failure_clustering_threshold=0.9,
    )

    orchestrator = Mock()
    orchestrator.build_report_facts.side_effect = ValueError("boom")
    service._analytics_orchestrator = orchestrator  # noqa: SLF001

    with pytest.raises(ReportingError, match="ValueError: boom"):
        service.generate(
            report_path=Path("report.json"),
            output_dir=Path("out"),
            environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
            report_format="pytest",
            enable_llm=True,
        )

    orchestrator.build_report_facts.assert_called_once()
    _, kwargs = orchestrator.build_report_facts.call_args
    assert kwargs["failure_clustering_threshold"] == 0.9


def test_report_generation_unknown_format_raises_configuration_error() -> None:
    """Requesting an unregistered format should raise ConfigurationError before parsing."""
    parsers = _make_parsers()
    writer = Mock()
    service = ReportGenerationService(parsers, writer)

    with pytest.raises(ConfigurationError, match="unknown-format"):
        service.generate(
            report_path=Path("report.json"),
            output_dir=Path("out"),
            environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
            report_format="unknown-format",
        )


def test_report_generation_tags_source_format_on_facts() -> None:
    """Generated ReportFacts should have source_format matching report_format."""
    parsers = _make_parsers()
    writer = Mock()
    writer.save_reports.return_value = (Path("summary.md"), Path("signoff.md"))
    service = ReportGenerationService(parsers, writer)

    service.generate(
        report_path=Path("report.json"),
        output_dir=Path("out"),
        environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
        report_format="pytest",
    )

    facts_arg = writer.save_reports.call_args.kwargs["facts"]
    assert facts_arg.source_format == "pytest"


def test_comparison_service_dispatches_to_correct_parser() -> None:
    """CompareReportsUseCase should use the parser matching report_format."""
    pytest_parser = Mock()
    pytest_parser.parse.return_value = _make_parsed_report()
    k6_parser = Mock()

    parsers: dict[str, Any] = {"pytest": pytest_parser, "k6": k6_parser}
    service = ReportComparisonService(parsers)
    service.compare(Path("a.json"), Path("b.json"), report_format="pytest")

    assert pytest_parser.parse.call_count == 2
    k6_parser.parse.assert_not_called()


def test_comparison_service_unknown_format_raises_error() -> None:
    """Unknown format in compare should raise ConfigurationError."""
    service = ReportComparisonService({"pytest": Mock()})
    with pytest.raises(ConfigurationError, match="bad"):
        service.compare(Path("a.json"), Path("b.json"), report_format="bad")


def test_validation_service_dispatches_to_correct_parser() -> None:
    """ValidateReportUseCase should use the parser matching report_format."""
    parser = Mock()
    parser.parse.return_value = _make_parsed_report()
    service = ReportValidationService({"pytest": parser})

    result = service.validate_report(Path("r.json"), report_format="pytest")

    parser.parse.assert_called_once_with(Path("r.json"))
    assert result == _make_parsed_report().metrics


def test_validation_service_unknown_format_raises_error() -> None:
    """Unknown format in validate_report should raise ConfigurationError."""
    service = ReportValidationService({"pytest": Mock()})
    with pytest.raises(ConfigurationError, match="nope"):
        service.validate_report(Path("r.json"), report_format="nope")


def test_k6_summary_table_service_generates_table(tmp_path: Path) -> None:
    """K6 summary service should parse each JSON report and write one consolidated table."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    first = reports_dir / "b-report.json"
    second = reports_dir / "a-report.json"
    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")

    parser = Mock()
    first_row = Mock(name="first-row")
    second_row = Mock(name="second-row")
    parser.parse_summary_row.side_effect = [first_row, second_row]
    writer = Mock()

    service = K6SummaryTableService(parser=parser, writer=writer)
    out_file = tmp_path / "out" / "performance_summary.md"

    result = service.generate_k6_summary_table(reports_dir=reports_dir, output_path=out_file)

    assert result.output_path == out_file
    assert result.rows_count == 2
    parsed_paths = [call_args.args[0] for call_args in parser.parse_summary_row.call_args_list]
    assert parsed_paths == [second, first]
    writer.write_summary_table.assert_called_once_with([first_row, second_row], out_file)


def test_k6_summary_table_service_missing_directory_raises_error(tmp_path: Path) -> None:
    """K6 summary service should reject non-existent directories."""
    service = K6SummaryTableService(parser=Mock(), writer=Mock())
    with pytest.raises(ConfigurationError, match="Reports directory not found"):
        service.generate_k6_summary_table(
            reports_dir=tmp_path / "missing",
            output_path=tmp_path / "out" / "summary.md",
        )


def test_k6_summary_table_service_empty_directory_raises_error(tmp_path: Path) -> None:
    """K6 summary service should reject directories without JSON reports."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    service = K6SummaryTableService(parser=Mock(), writer=Mock())
    with pytest.raises(ConfigurationError, match="No JSON report files found"):
        service.generate_k6_summary_table(
            reports_dir=reports_dir,
            output_path=tmp_path / "out" / "summary.md",
        )


def test_k6_summary_table_service_wraps_unexpected_errors(tmp_path: Path) -> None:
    """K6 summary service should wrap unexpected parser failures into ReportingError."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report_file = reports_dir / "report.json"
    report_file.write_text("{}", encoding="utf-8")

    parser = Mock()
    parser.parse_summary_row.side_effect = ValueError("boom")
    service = K6SummaryTableService(parser=parser, writer=Mock())

    with pytest.raises(ReportingError, match="Failed to generate consolidated k6 summary table"):
        service.generate_k6_summary_table(
            reports_dir=reports_dir,
            output_path=tmp_path / "out" / "summary.md",
        )
