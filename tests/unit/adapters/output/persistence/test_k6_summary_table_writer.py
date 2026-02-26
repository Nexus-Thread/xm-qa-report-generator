"""Unit tests for consolidated k6 summary markdown writer."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from qa_report_generator.adapters.output.persistence.performance import K6SummaryTableMarkdownWriter
from qa_report_generator.domain.exceptions import PersistenceError
from qa_report_generator.domain.models import K6SummaryRow

if TYPE_CHECKING:
    from pathlib import Path


def _row(
    *,
    scenario: str,
    outcome_passed: bool,
    error_rate_percent: float,
    achieved_rps: float,
) -> K6SummaryRow:
    return K6SummaryRow(
        service="THD",
        scenario=scenario,
        target_load_rps=40,
        duration_seconds=900,
        thresholds=["p(95)<100", "p(99)<200", "rate<0.1"],
        iterations=36000,
        achieved_rps=achieved_rps,
        latency_med_ms=110.0,
        latency_p95_ms=190.0,
        latency_p99_ms=255.0,
        latency_max_ms=1500.0,
        error_rate_percent=error_rate_percent,
        outcome_passed=outcome_passed,
    )


def test_write_summary_table_writes_markdown(tmp_path: Path) -> None:
    """Writer should persist markdown with header and formatted scenario rows."""
    writer = K6SummaryTableMarkdownWriter()
    output_path = tmp_path / "out" / "performance_summary.md"

    written = writer.write_summary_table(
        [
            _row(scenario="zzzScenario", outcome_passed=True, error_rate_percent=0.0, achieved_rps=40.0),
            _row(scenario="aaaScenario", outcome_passed=False, error_rate_percent=3.0, achieved_rps=39.6),
        ],
        output_path,
    )

    assert written == output_path
    content = output_path.read_text(encoding="utf-8")
    assert content.startswith("# Summary")
    assert "| Service | Scenario | Target load (rps) |" in content
    assert content.index("aaaScenario") < content.index("zzzScenario")
    assert "✅ Passed" in content
    assert "❌ Failed" in content
    assert "http_req_failed < 10%" in content
    assert "3.0%" in content


def test_write_summary_table_wraps_os_errors(tmp_path: Path) -> None:
    """Writer should raise PersistenceError when output path cannot be written."""
    writer = K6SummaryTableMarkdownWriter()
    existing_dir = tmp_path / "existing-dir"
    existing_dir.mkdir()

    with pytest.raises(PersistenceError, match="Failed to write k6 summary table"):
        writer.write_summary_table(
            [_row(scenario="scenario", outcome_passed=True, error_rate_percent=0.0, achieved_rps=40.0)],
            existing_dir,
        )
