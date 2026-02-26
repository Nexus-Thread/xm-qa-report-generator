"""Unit tests for the k6-only CLI adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from typer.testing import CliRunner

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.application.dtos import AppSettings

if TYPE_CHECKING:
    from pathlib import Path


def _make_generation_result(tmp_path: Path) -> Mock:
    summary = tmp_path / "pytest_summary.md"
    signoff = tmp_path / "signoff_report.md"
    summary.write_text("summary", encoding="utf-8")
    signoff.write_text("signoff", encoding="utf-8")
    return Mock(
        summary_path=summary,
        signoff_path=signoff,
        parse_duration=0.1,
        write_duration=0.2,
        total_duration=0.3,
    )


def _make_k6_adapter() -> tuple[K6CliAdapter, Mock, Mock]:
    generate_use_case = Mock()
    generate_k6_summary_table_use_case = Mock()
    compare_use_case = Mock()
    validate_use_case = Mock()

    adapter = K6CliAdapter(
        generate_use_case,
        generate_k6_summary_table_use_case,
        compare_use_case,
        validate_use_case,
        config=AppSettings(),
    )
    return adapter, generate_use_case, generate_k6_summary_table_use_case


def _runner() -> CliRunner:
    return CliRunner()


def test_k6_cli_exposes_only_generate_and_k6_summary_commands() -> None:
    """k6 CLI should expose only generate and k6-summary commands."""
    adapter, _, _ = _make_k6_adapter()

    result = _runner().invoke(adapter._app, ["--help"])  # noqa: SLF001

    assert result.exit_code == 0
    assert "generate" in result.stdout
    assert "k6-summary" in result.stdout
    assert "diff" not in result.stdout
    assert "validate-config" not in result.stdout


def test_k6_generate_hardwires_k6_report_format(tmp_path: Path) -> None:
    """Generate command should always pass report_format='k6'."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter, generate_use_case, _ = _make_k6_adapter()
    generate_use_case.generate.return_value = _make_generation_result(tmp_path)

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 0
    _, kwargs = generate_use_case.generate.call_args
    assert kwargs["report_format"] == "k6"


def test_k6_generate_does_not_expose_format_option(tmp_path: Path) -> None:
    """k6-only generate command should reject --format option."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    adapter, _, _ = _make_k6_adapter()

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(tmp_path / "out"),
            "--format",
            "k6",
        ],
    )

    assert result.exit_code == 2
    output = result.stdout + result.stderr
    assert "No such option: --format" in output


def test_k6_summary_command_invokes_use_case(tmp_path: Path) -> None:
    """k6-summary should invoke the summary use case."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    out_file = tmp_path / "out" / "performance_summary.md"

    adapter, _, summary_use_case = _make_k6_adapter()
    summary_use_case.generate_k6_summary_table.return_value = Mock(output_path=out_file, rows_count=2)

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "k6-summary",
            "--reports-dir",
            str(reports_dir),
            "--out-file",
            str(out_file),
        ],
    )

    assert result.exit_code == 0
    summary_use_case.generate_k6_summary_table.assert_called_once_with(
        reports_dir=reports_dir,
        output_path=out_file,
    )
