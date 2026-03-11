"""Unit tests for executive summary builders."""

from __future__ import annotations

from qa_report_generator.domain.analytics import (
    build_overall_executive_summary,
    build_scenario_executive_summary,
)


def test_build_scenario_executive_summary_uses_prebuilt_threshold_results() -> None:
    """Scenario executive summary uses attached threshold results for status and note."""
    run_payload = {
        "scenario": {
            "name": "megatron-load",
            "env_name": "staging",
            "executor": "constant-arrival-rate",
            "rate": 10,
            "duration": "1m",
            "preAllocatedVUs": 10,
            "maxVUs": 20,
        },
        "threshold_results": [
            {
                "metric_key": "http_req_duration",
                "expression": "p(95)<1000",
                "status": "pass",
            },
            {
                "metric_key": "checks",
                "expression": "rate>0.99",
                "status": "fail",
            },
        ],
    }

    result = build_scenario_executive_summary(
        run_payload=run_payload,
        source_report_files=["report.json"],
    )

    assert result.scenario_name == "megatron-load"
    assert result.status == "fail"
    assert result.source_report_files == ("report.json",)
    assert len(result.threshold_results) == 2
    assert "checks:rate>0.99" in result.executive_note


def test_build_overall_executive_summary_rolls_up_attention_scenarios() -> None:
    """Overall executive summary reports failing scenarios and counts."""
    pass_summary = build_scenario_executive_summary(
        run_payload={
            "scenario": {"name": "scenario-a"},
            "threshold_results": [{"metric_key": "checks", "expression": "rate>0.99", "status": "pass"}],
        },
        source_report_files=["a.json"],
    )
    fail_summary = build_scenario_executive_summary(
        run_payload={
            "scenario": {"name": "scenario-b"},
            "threshold_results": [{"metric_key": "checks", "expression": "rate>0.99", "status": "fail"}],
        },
        source_report_files=["b.json"],
    )

    result = build_overall_executive_summary(
        scenario_summaries=[pass_summary, fail_summary],
    )

    assert result.status == "fail"
    assert result.total_scenarios == 2
    assert result.passed_scenarios == 1
    assert result.failed_scenarios == 1
    assert result.scenarios_requiring_attention == ("scenario-b",)
