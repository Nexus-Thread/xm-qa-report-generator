"""Unit tests for the k6-only CLI adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from typer.testing import CliRunner

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.domain.exceptions import ReportingError

if TYPE_CHECKING:
    from pathlib import Path


def _make_k6_adapter() -> tuple[K6CliAdapter, Mock]:
    generate_k6_summary_table_use_case = Mock()

    adapter = K6CliAdapter(generate_k6_summary_table_use_case)
    return adapter, generate_k6_summary_table_use_case


def _runner() -> CliRunner:
    return CliRunner()


def test_k6_cli_exposes_only_generate_command() -> None:
    """k6 CLI should expose only generate command."""
    adapter, _ = _make_k6_adapter()

    result = _runner().invoke(adapter._app, ["--help"])  # noqa: SLF001

    assert result.exit_code == 0
    assert "generate" in result.stdout
    assert "k6-summary" not in result.stdout
    assert "diff" not in result.stdout
    assert "validate-config" not in result.stdout


def test_k6_generate_accepts_single_report_file(tmp_path: Path) -> None:
    """Generate command should pass a single report file to the use case."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    out_file = tmp_path / "out" / "performance_summary.md"

    adapter, summary_use_case = _make_k6_adapter()
    summary_use_case.generate_k6_summary_table.return_value = Mock(output_path=out_file, rows_count=1)

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--report",
            str(report_path),
            "--out-file",
            str(out_file),
        ],
    )

    assert result.exit_code == 0
    summary_use_case.generate_k6_summary_table.assert_called_once_with(
        report_files=[report_path],
        output_path=out_file,
    )


def test_k6_generate_accepts_directory_and_multiple_reports(tmp_path: Path) -> None:
    """Generate command should resolve report directories and repeated report options."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    report_b = reports_dir / "b-report.json"
    report_a = reports_dir / "a-report.json"
    report_b.write_text("{}", encoding="utf-8")
    report_a.write_text("{}", encoding="utf-8")
    extra_report = tmp_path / "c-report.json"
    extra_report.write_text("{}", encoding="utf-8")

    out_file = tmp_path / "out" / "performance_summary.md"
    adapter, summary_use_case = _make_k6_adapter()
    summary_use_case.generate_k6_summary_table.return_value = Mock(output_path=out_file, rows_count=3)

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--report",
            str(reports_dir),
            "--report",
            str(extra_report),
            "--report",
            str(report_b),
            "--out-file",
            str(out_file),
        ],
    )

    assert result.exit_code == 0
    expected_report_files = sorted({report_a, report_b, extra_report})
    summary_use_case.generate_k6_summary_table.assert_called_once_with(
        report_files=expected_report_files,
        output_path=out_file,
    )


def test_k6_generate_rejects_non_json_report_file(tmp_path: Path) -> None:
    """Generate command should reject non-JSON report files."""
    report_path = tmp_path / "report.txt"
    report_path.write_text("not-json", encoding="utf-8")

    adapter, summary_use_case = _make_k6_adapter()

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 1
    assert "Report file must be a JSON file" in result.stdout
    summary_use_case.generate_k6_summary_table.assert_not_called()


def test_k6_generate_rejects_directory_without_json_reports(tmp_path: Path) -> None:
    """Generate command should reject directories that contain no JSON files."""
    reports_dir = tmp_path / "empty-reports"
    reports_dir.mkdir()

    adapter, summary_use_case = _make_k6_adapter()

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--report",
            str(reports_dir),
        ],
    )

    assert result.exit_code == 1
    assert "No JSON report files found in directory" in result.stdout
    summary_use_case.generate_k6_summary_table.assert_not_called()


def test_k6_generate_handles_reporting_error(tmp_path: Path) -> None:
    """Generate command should translate ReportingError to exit code 1."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter, summary_use_case = _make_k6_adapter()
    summary_use_case.generate_k6_summary_table.side_effect = ReportingError(
        "summary failure",
        suggestion="Check report content",
    )

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--report",
            str(report_path),
        ],
    )

    assert result.exit_code == 1
    assert "summary failure" in result.stdout
    assert "Check report content" in result.stdout
