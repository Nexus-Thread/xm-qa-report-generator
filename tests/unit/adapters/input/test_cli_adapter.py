"""Unit tests for the CLI adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from typer.testing import CliRunner

from qa_report_generator.adapters.input.cli_adapter import CliAdapter
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.config import PreprocessingProfile
from qa_report_generator.domain.exceptions import ReportingError
from qa_report_generator.domain.models import RunMetrics
from qa_report_generator.domain.value_objects import Duration

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.ports.input import ReportGenerationResult


def _make_metrics(total: int = 3, failed: int = 1, skipped: int = 0) -> RunMetrics:
    passed = total - failed - skipped
    return RunMetrics(
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        errors=0,
        duration=Duration(seconds=1.2),
        failures=[],
    )


def _make_generation_result(tmp_path: Path) -> ReportGenerationResult:
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


def _make_adapter(config: AppSettings | None = None) -> tuple[CliAdapter, Mock, Mock, Mock]:
    generate_use_case = Mock()
    generate_k6_summary_table_use_case = Mock()
    compare_use_case = Mock()
    validate_use_case = Mock()
    effective_config = config or AppSettings()
    adapter = CliAdapter(
        generate_use_case,
        generate_k6_summary_table_use_case,
        compare_use_case,
        validate_use_case,
        config=effective_config,
    )
    return adapter, generate_use_case, compare_use_case, validate_use_case


def _make_adapter_with_k6_summary(config: AppSettings | None = None) -> tuple[CliAdapter, Mock]:
    generate_use_case = Mock()
    generate_k6_summary_table_use_case = Mock()
    compare_use_case = Mock()
    validate_use_case = Mock()
    effective_config = config or AppSettings()
    adapter = CliAdapter(
        generate_use_case,
        generate_k6_summary_table_use_case,
        compare_use_case,
        validate_use_case,
        config=effective_config,
    )
    return adapter, generate_k6_summary_table_use_case


def _runner() -> CliRunner:
    return CliRunner()


def test_generate_dry_run_happy_path(tmp_path: Path) -> None:
    """Dry-run should validate inputs and parse JSON without generating reports."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    output_dir = tmp_path / "out"
    adapter, generate_use_case, _, validate_use_case = _make_adapter(config=AppSettings())
    validate_use_case.validate_report.return_value = _make_metrics(total=5, failed=1, skipped=1)

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(output_dir),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert "Dry-run validation passed" in result.stdout
    generate_use_case.generate.assert_not_called()


def test_generate_dry_run_parse_failure(tmp_path: Path) -> None:
    """Dry-run should return non-zero when parser fails."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    output_dir = tmp_path / "out"
    adapter, _, _, validate_use_case = _make_adapter(config=AppSettings())
    validate_use_case.validate_report.side_effect = ValueError("boom")

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(output_dir),
            "--dry-run",
        ],
    )

    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "Failed to parse JSON" in output


def test_generate_rejects_missing_report(tmp_path: Path) -> None:
    """Missing input file should fail validation."""
    adapter, _, _, _ = _make_adapter(config=AppSettings())

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(tmp_path / "missing.json"),
            "--out",
            str(tmp_path / "out"),
        ],
    )

    assert result.exit_code == 2
    output = result.stdout + result.stderr
    assert "Invalid value for '--json-report'" in output or "does not exist" in output


def test_generate_creates_output_directory(tmp_path: Path) -> None:
    """Generate command should create output directory and invoke use case."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    output_dir = tmp_path / "out"
    adapter, generate_use_case, _, _ = _make_adapter(config=AppSettings())
    generation_result = _make_generation_result(tmp_path)
    generate_use_case.generate.return_value = generation_result

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert output_dir.exists()
    generate_use_case.generate.assert_called_once()


def test_generate_handles_reporting_error(tmp_path: Path) -> None:
    """Reporting errors should be rendered with the error message and exit 1."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    adapter, generate_use_case, _, _ = _make_adapter(config=AppSettings())
    generate_use_case.generate.side_effect = ReportingError("boom")

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

    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "boom" in output


def test_generate_resolves_verbosity_flags(tmp_path: Path) -> None:
    """Using both quiet and verbose should fail validation."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    adapter, _, _, _ = _make_adapter(config=AppSettings())

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(tmp_path / "out"),
            "--quiet",
            "--verbose",
        ],
    )

    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "Cannot use both" in output


def test_generate_profile_invalid_value(tmp_path: Path) -> None:
    """Invalid profile values should be rejected."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    adapter, _, _, _ = _make_adapter(config=AppSettings())

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(tmp_path / "out"),
            "--profile",
            "invalid",
        ],
    )

    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "Invalid preprocessing profile" in output


def test_generate_profile_applies_defaults(tmp_path: Path) -> None:
    """Valid profiles should update config defaults before generation."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    adapter, generate_use_case, _, _ = _make_adapter()
    generate_use_case.generate.return_value = _make_generation_result(tmp_path)

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(tmp_path / "out"),
            "--profile",
            PreprocessingProfile.MINIMAL.value,
        ],
    )

    assert result.exit_code == 0
    assert generate_use_case.generate.called


def test_generate_no_llm_disables_llm_flag(tmp_path: Path) -> None:
    """--no-llm should disable narrative generation."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    adapter, generate_use_case, _, _ = _make_adapter(config=AppSettings())
    generate_use_case.generate.return_value = _make_generation_result(tmp_path)

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(tmp_path / "out"),
            "--no-llm",
        ],
    )

    assert result.exit_code == 0
    _, kwargs = generate_use_case.generate.call_args
    assert kwargs["enable_llm"] is False
    assert kwargs["report_format"] == "pytest"


def test_generate_max_failures_minus_one_disables_limit(tmp_path: Path) -> None:
    """--max-failures -1 should disable failure limiting."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    adapter, generate_use_case, _, _ = _make_adapter(config=AppSettings())
    generate_use_case.generate.return_value = _make_generation_result(tmp_path)

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(tmp_path / "out"),
            "--max-failures",
            "-1",
        ],
    )

    assert result.exit_code == 0
    _, kwargs = generate_use_case.generate.call_args
    assert kwargs["max_failures"] is None


def test_generate_format_k6_passes_format_to_use_case(tmp_path: Path) -> None:
    """--format k6 should pass report_format='k6' to the use case."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    adapter, generate_use_case, _, _ = _make_adapter(config=AppSettings())
    generate_use_case.generate.return_value = _make_generation_result(tmp_path)

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

    assert result.exit_code == 0
    _, kwargs = generate_use_case.generate.call_args
    assert kwargs["report_format"] == "k6"


def test_diff_format_k6_passes_format_to_compare(tmp_path: Path) -> None:
    """Diff --format k6 should pass report_format='k6' to the compare use case."""
    report_a = tmp_path / "a.json"
    report_b = tmp_path / "b.json"
    report_a.write_text("{}", encoding="utf-8")
    report_b.write_text("{}", encoding="utf-8")
    adapter, _, compare_use_case, _ = _make_adapter(config=AppSettings())
    compare_use_case.compare.return_value = Mock(new_failures=[], fixed_tests=[], regressions=[])

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "diff",
            "--report-a",
            str(report_a),
            "--report-b",
            str(report_b),
            "--format",
            "k6",
        ],
    )

    assert result.exit_code == 0
    _, kwargs = compare_use_case.compare.call_args
    assert kwargs["report_format"] == "k6"


def test_validate_config_command() -> None:
    """Validate-config should render configuration summary."""
    config = AppSettings(llm_base_url="http://test", llm_model="model", llm_timeout=10.0)
    adapter, _, _, _ = _make_adapter(config=config)
    result = _runner().invoke(adapter._app, ["validate-config"])  # noqa: SLF001

    assert result.exit_code == 0
    assert "Configuration is valid" in result.stdout


def test_diff_command_renders_summary(tmp_path: Path) -> None:
    """Diff command should render summary table and lists."""
    report_a = tmp_path / "a.json"
    report_b = tmp_path / "b.json"
    report_a.write_text("{}", encoding="utf-8")
    report_b.write_text("{}", encoding="utf-8")
    adapter, _, compare_use_case, _ = _make_adapter(config=AppSettings())
    compare_use_case.compare.return_value = Mock(
        new_failures=[Mock(suite="tests", name="test_new")],
        fixed_tests=[Mock(suite="tests", name="test_fixed")],
        regressions=[Mock(suite="tests", name="test_regress")],
    )

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "diff",
            "--report-a",
            str(report_a),
            "--report-b",
            str(report_b),
        ],
    )

    assert result.exit_code == 0
    assert "Report Diff Summary" in result.stdout
    assert "Regressions" in result.stdout
    compare_use_case.compare.assert_called_once()


def test_generate_rejects_max_failures_below_minus_one(tmp_path: Path) -> None:
    """Values below -1 for --max-failures should be rejected by CLI validation."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")
    adapter, _, _, _ = _make_adapter(config=AppSettings())

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "generate",
            "--json-report",
            str(report_path),
            "--out",
            str(tmp_path / "out"),
            "--max-failures",
            "-2",
        ],
    )

    assert result.exit_code == 2
    output = result.stdout + result.stderr
    assert "-1" in output


def test_diff_command_handles_reporting_error(tmp_path: Path) -> None:
    """Diff command should translate reporting errors into CLI exit code 1."""
    report_a = tmp_path / "a.json"
    report_b = tmp_path / "b.json"
    report_a.write_text("{}", encoding="utf-8")
    report_b.write_text("{}", encoding="utf-8")
    adapter, _, compare_use_case, _ = _make_adapter(config=AppSettings())
    compare_use_case.compare.side_effect = ReportingError("boom")

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "diff",
            "--report-a",
            str(report_a),
            "--report-b",
            str(report_b),
        ],
    )

    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "boom" in output


def test_k6_summary_command_invokes_use_case(tmp_path: Path) -> None:
    """k6-summary should call summary-table use case and print output path."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    out_file = tmp_path / "out" / "performance_summary.md"

    adapter, k6_summary_use_case = _make_adapter_with_k6_summary(config=AppSettings())
    k6_summary_use_case.generate_k6_summary_table.return_value = Mock(output_path=out_file, rows_count=3)

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
    output = result.stdout + result.stderr
    assert "K6 summary table" in output
    assert "Rows: 3" in output
    k6_summary_use_case.generate_k6_summary_table.assert_called_once_with(
        reports_dir=reports_dir,
        output_path=out_file,
    )


def test_k6_summary_command_handles_reporting_error(tmp_path: Path) -> None:
    """k6-summary should translate ReportingError to exit code 1."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    adapter, k6_summary_use_case = _make_adapter_with_k6_summary(config=AppSettings())
    k6_summary_use_case.generate_k6_summary_table.side_effect = ReportingError("broken summary")

    result = _runner().invoke(
        adapter._app,  # noqa: SLF001
        [
            "k6-summary",
            "--reports-dir",
            str(reports_dir),
        ],
    )

    assert result.exit_code == 1
    output = result.stdout + result.stderr
    assert "broken summary" in output
