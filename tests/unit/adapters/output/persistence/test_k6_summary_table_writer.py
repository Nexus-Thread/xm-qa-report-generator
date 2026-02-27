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
        executor="constant-arrival-rate",
        time_unit="1s",
        pre_allocated_vus=100,
        max_vus=1000,
        observed_vus_current=6,
        observed_vus_peak=11,
        total_requests=36120,
        dropped_iterations=12,
        checks_passes=36120,
        checks_fails=0,
        target_load_rps=40,
        duration_seconds=900,
        thresholds={
            "http_req_duration": ["p(95)<100", "p(99)<200"],
            "http_req_failed": ["rate<0.1"],
        },
        iterations=36000,
        achieved_rps=achieved_rps,
        latency_metrics_ms={
            "min": 60.0,
            "avg": 130.0,
            "med": 110.0,
            "p(95)": 190.0,
            "p(99)": 255.0,
            "max": 1500.0,
        },
        waiting_metrics_ms={
            "med": 108.0,
            "p(95)": 188.0,
            "p(99)": 250.0,
            "max": 1400.0,
        },
        connecting_metrics_ms={
            "med": 0.0,
            "p(95)": 0.0,
            "p(99)": 0.0,
        },
        tls_handshaking_metrics_ms={
            "med": 0.0,
            "p(95)": 0.0,
            "p(99)": 0.0,
        },
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
    assert (
        "| Service | Scenario | Executor | Time unit | VUs (pre/max) | Observed VUs (cur/peak) | Duration | Load expected (rps) | Load actual (rps) | "
        "Error rate expected (%) | Error rate actual (%) | p95 expected (ms) | p95 actual (ms) | "
        "p99 expected (ms) | p99 actual (ms) | Outcome | Comment |" in content
    )
    assert content.index("aaaScenario") < content.index("zzzScenario")
    assert "✅ Passed" in content
    assert "❌ Failed" in content
    assert "39.60" in content
    assert "40.00" in content
    assert "10.0" in content
    assert "3.0" in content
    assert "100" in content
    assert "190" in content
    assert "200" in content
    assert "255" in content
    assert "constant-arrival-rate" in content
    assert "1s" in content
    assert "100/1000" in content
    assert "6/11" in content
    assert "## Scenario & Load Model" in content
    assert "| Scenario | Executor | Time unit | VUs (pre/max) | Observed VUs (cur/peak) | Duration | Target load (rps) |" in content
    assert "| aaaScenario | constant-arrival-rate | 1s | 100/1000 | 6/11 | 15m | 40 |" in content
    assert "| zzzScenario | constant-arrival-rate | 1s | 100/1000 | 6/11 | 15m | 40 |" in content
    assert content.index("## Scenario & Load Model") > content.index("| Service | Scenario")
    assert "## Performance Results" in content
    assert "#### 4.1 Throughput & stability" in content
    assert "- Total requests: 36120" in content
    assert "- Dropped iterations: 12" in content
    assert "#### 4.2 Errors" in content
    assert "- Checks: 36120 passes, 0 fails" in content
    assert "#### 4.3 Latency" in content
    assert "- aaaScenario (http_req_duration{test_name:aaaScenario})" in content
    assert "Interpretation: *[LLM placeholder" in content
    assert "iters /" not in content
    assert "rate <" not in content


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
