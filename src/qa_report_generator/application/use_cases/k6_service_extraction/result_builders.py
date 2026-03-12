"""Result building helpers for k6 extraction use case."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6ServiceExtractionRun
from qa_report_generator.domain.analytics import (
    analyze_overall_scenarios,
    analyze_scenario_run,
    build_overall_executive_summary,
    build_scenario_executive_summary,
)

from .source_payload import (
    extract_env_name,
    normalize_metric_payloads_copy,
    normalize_threshold_definitions_from_source_payload,
    pick_scenario_config,
    pick_test_run_duration_ms,
)
from .thresholds import build_threshold_summaries_from_source_payload

if TYPE_CHECKING:
    from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario


def build_generic_result(*, parsed_report: K6ParsedReport) -> K6ServiceExtractionResult:
    """Build generic parsed output when no service definition exists."""
    runs = [
        K6ServiceExtractionRun(
            source_report_files=(scenario.source_report_file,),
            extracted={
                "service": parsed_report.service,
                "scenario": _build_generic_scenario_payload(scenario=scenario),
                "test_run_duration_ms": pick_test_run_duration_ms(source_payload=scenario.source_payload),
                "thresholds": {
                    metric_key: list(expressions)
                    for metric_key, expressions in normalize_threshold_definitions_from_source_payload(
                        source_payload=scenario.source_payload,
                    ).items()
                },
                "threshold_results": [
                    {
                        "metric_key": threshold.metric_key,
                        "expression": threshold.expression,
                        "status": threshold.status,
                    }
                    for threshold in build_threshold_summaries_from_source_payload(
                        source_payload=scenario.source_payload,
                    )
                ],
                "metrics": normalize_metric_payloads_copy(source_payload=scenario.source_payload),
            },
        )
        for scenario in parsed_report.scenarios
    ]
    scenario_analyses = [
        analyze_scenario_run(
            run_payload=run.extracted,
            source_report_files=run.source_report_files,
        )
        for run in runs
    ]
    overall_analysis = analyze_overall_scenarios(scenario_analyses=scenario_analyses)
    scenario_summaries = [build_scenario_executive_summary(analysis=analysis) for analysis in scenario_analyses]
    return K6ServiceExtractionResult(
        service=parsed_report.service,
        mode="generic",
        runs=runs,
        overall_summary=build_overall_executive_summary(analysis=overall_analysis),
        scenario_summaries=scenario_summaries,
    )


def _build_generic_scenario_payload(*, scenario: K6Scenario) -> dict[str, Any]:
    """Build generic scenario metadata from raw source payload."""
    scenario_config = pick_scenario_config(
        source_payload=scenario.source_payload,
        scenario_name=scenario.name,
    )
    return {
        "name": scenario.name,
        "env_name": extract_env_name(scenario_config=scenario_config),
        "executor": _as_string(scenario_config.get("executor")) or "",
        "rate": _as_float(scenario_config.get("rate")),
        "duration": _as_string(scenario_config.get("duration")) or "",
        "pre_allocated_vus": _as_int(scenario_config.get("preAllocatedVUs") or scenario_config.get("pre_allocated_vus")),
        "max_vus": _as_int(scenario_config.get("maxVUs") or scenario_config.get("max_vus")),
    }


def _as_string(value: Any) -> str | None:
    """Return a non-empty string value when available."""
    return value if isinstance(value, str) and value else None


def _as_float(value: Any) -> float:
    """Return a numeric value as float or zero when absent."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _as_int(value: Any) -> int:
    """Return an integer value or zero when absent."""
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return value
