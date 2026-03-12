"""Domain services that project analysis into executive summaries."""

from __future__ import annotations

from qa_report_generator.domain.analytics.models import (
    K6OverallAnalysis,
    K6OverallExecutiveSummary,
    K6ScenarioAnalysis,
    K6ScenarioExecutiveSummary,
)


def build_scenario_executive_summary(*, analysis: K6ScenarioAnalysis) -> K6ScenarioExecutiveSummary:
    """Project scenario analysis into a final scenario summary row."""
    return K6ScenarioExecutiveSummary(
        scenario_name=analysis.scenario_name,
        env_name=analysis.env_name,
        source_report_files=analysis.source_report_files,
        status=analysis.status,
        executor=analysis.executor,
        rate=analysis.rate,
        duration=analysis.duration,
        pre_allocated_vus=analysis.pre_allocated_vus,
        max_vus=analysis.max_vus,
        threshold_results=analysis.threshold_results,
        executive_note=_build_scenario_executive_note(analysis=analysis),
    )


def build_overall_executive_summary(*, analysis: K6OverallAnalysis) -> K6OverallExecutiveSummary:
    """Project overall analysis into a final overall summary row."""
    return K6OverallExecutiveSummary(
        status=analysis.status,
        total_scenarios=analysis.total_scenarios,
        passed_scenarios=analysis.passed_scenarios,
        failed_scenarios=analysis.failed_scenarios,
        unknown_scenarios=analysis.unknown_scenarios,
        scenarios_requiring_attention=analysis.scenarios_requiring_attention,
        executive_summary=_build_overall_executive_text(analysis=analysis),
    )


def _build_scenario_executive_note(*, analysis: K6ScenarioAnalysis) -> str:
    """Build concise scenario narrative from scenario analysis facts."""
    if analysis.status == "pass":
        return f"Scenario {analysis.scenario_name} met all evaluated thresholds."
    if analysis.status == "fail":
        if analysis.failing_thresholds:
            return f"Scenario {analysis.scenario_name} requires attention due to failing thresholds: " + ", ".join(analysis.failing_thresholds)
        return f"Scenario {analysis.scenario_name} requires attention due to threshold failures."
    return f"Scenario {analysis.scenario_name} has no threshold evaluation data available yet."


def _build_overall_executive_text(*, analysis: K6OverallAnalysis) -> str:
    """Build concise overall narrative from aggregate analysis facts."""
    if analysis.total_scenarios == 0:
        return "No scenarios were available to summarize."
    if analysis.status == "pass":
        return f"All {analysis.total_scenarios} scenarios passed their evaluated thresholds."
    if analysis.status == "fail":
        return f"{analysis.failed_scenarios} of {analysis.total_scenarios} scenarios failed threshold evaluation and require attention."
    return f"{analysis.unknown_scenarios} of {analysis.total_scenarios} scenarios are missing threshold evaluation data."
