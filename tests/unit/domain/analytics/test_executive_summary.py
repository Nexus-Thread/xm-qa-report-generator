"""Unit tests for executive summary builders."""

from __future__ import annotations

from qa_report_generator.domain.analytics import (
    analyze_overall_scenarios,
    analyze_scenario_run,
    build_overall_executive_summary,
    build_scenario_executive_summary,
)


def test_analyze_scenario_run_uses_prebuilt_threshold_results() -> None:
    """Scenario analysis uses attached threshold results for status and failures."""
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

    result = analyze_scenario_run(
        run_payload=run_payload,
        source_report_files=["report.json"],
    )

    assert result.scenario_name == "megatron-load"
    assert result.status == "fail"
    assert result.source_report_files == ("report.json",)
    assert len(result.threshold_results) == 2
    assert result.failing_thresholds == ("checks:rate>0.99",)


def test_build_scenario_executive_summary_projects_analysis_into_note() -> None:
    """Scenario executive summary builds narrative from scenario analysis."""
    analysis = analyze_scenario_run(
        run_payload={
            "scenario": {"name": "scenario-b"},
            "threshold_results": [{"metric_key": "checks", "expression": "rate>0.99", "status": "fail"}],
        },
        source_report_files=["b.json"],
    )

    result = build_scenario_executive_summary(analysis=analysis)

    assert result.status == "fail"
    assert result.source_report_files == ("b.json",)
    assert "checks:rate>0.99" in result.executive_note


def test_analyze_overall_scenarios_rolls_up_attention_scenarios() -> None:
    """Overall analysis reports failing scenarios and counts."""
    pass_analysis = analyze_scenario_run(
        run_payload={
            "scenario": {"name": "scenario-a"},
            "threshold_results": [{"metric_key": "checks", "expression": "rate>0.99", "status": "pass"}],
        },
        source_report_files=["a.json"],
    )
    fail_analysis = analyze_scenario_run(
        run_payload={
            "scenario": {"name": "scenario-b"},
            "threshold_results": [{"metric_key": "checks", "expression": "rate>0.99", "status": "fail"}],
        },
        source_report_files=["b.json"],
    )

    result = analyze_overall_scenarios(
        scenario_analyses=[pass_analysis, fail_analysis],
    )

    assert result.status == "fail"
    assert result.total_scenarios == 2
    assert result.passed_scenarios == 1
    assert result.failed_scenarios == 1
    assert result.scenarios_requiring_attention == ("scenario-b",)


def test_build_overall_executive_summary_projects_analysis_into_text() -> None:
    """Overall executive summary builds narrative from aggregate analysis."""
    analysis = analyze_overall_scenarios(
        scenario_analyses=[
            analyze_scenario_run(
                run_payload={
                    "scenario": {"name": "scenario-a"},
                    "threshold_results": [{"metric_key": "checks", "expression": "rate>0.99", "status": "pass"}],
                },
                source_report_files=["a.json"],
            ),
            analyze_scenario_run(
                run_payload={
                    "scenario": {"name": "scenario-b"},
                    "threshold_results": [{"metric_key": "checks", "expression": "rate>0.99", "status": "fail"}],
                },
                source_report_files=["b.json"],
            ),
        ]
    )

    result = build_overall_executive_summary(analysis=analysis)

    assert result.status == "fail"
    assert result.executive_summary == "1 of 2 scenarios failed threshold evaluation and require attention."
