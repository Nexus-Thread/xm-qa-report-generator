"""Result building helpers for k6 extraction use case."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6ServiceExtractionRun
from qa_report_generator.domain.analytics import (
    build_overall_executive_summary,
    build_scenario_executive_summary,
    build_threshold_summaries_from_source_payload,
)
from qa_report_generator.domain.exceptions import MissingK6ScenarioError

if TYPE_CHECKING:
    from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario


def build_generic_result(*, parsed_report: K6ParsedReport) -> K6ServiceExtractionResult:
    """Build generic parsed output when no service definition exists."""
    runs = [
        K6ServiceExtractionRun(
            source_report_files=[scenario.source_report_file],
            extracted={
                "service": parsed_report.service,
                "scenario": _build_generic_scenario_payload(scenario=scenario),
                "test_run_duration_ms": _test_run_duration_ms(source_payload=scenario.source_payload),
                "thresholds": _normalized_thresholds(source_payload=scenario.source_payload),
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
                "metrics": _normalized_metrics(source_payload=scenario.source_payload),
            },
        )
        for scenario in parsed_report.scenarios
    ]
    scenario_summaries = [
        build_scenario_executive_summary(
            run_payload=run.extracted,
            source_report_files=run.source_report_files,
        )
        for run in runs
    ]
    return K6ServiceExtractionResult(
        service=parsed_report.service,
        mode="generic",
        runs=runs,
        overall_summary=build_overall_executive_summary(scenario_summaries=scenario_summaries),
        scenario_summaries=scenario_summaries,
    )


def _build_generic_scenario_payload(*, scenario: K6Scenario) -> dict[str, Any]:
    """Build generic scenario metadata from raw source payload."""
    scenario_config = _pick_scenario_config(
        source_payload=scenario.source_payload,
        scenario_name=scenario.name,
    )
    return {
        "name": scenario.name,
        "env_name": _extract_env_name(scenario_config.get("tags")),
        "executor": _as_string(scenario_config.get("executor")) or "",
        "rate": _as_float(scenario_config.get("rate")),
        "duration": _as_string(scenario_config.get("duration")) or "",
        "pre_allocated_vus": _as_int(scenario_config.get("preAllocatedVUs") or scenario_config.get("pre_allocated_vus")),
        "max_vus": _as_int(scenario_config.get("maxVUs") or scenario_config.get("max_vus")),
    }


def _pick_scenario_config(*, source_payload: dict[str, Any], scenario_name: str) -> dict[str, Any]:
    """Return the selected scenario config from execScenarios."""
    scenarios = source_payload.get("execScenarios")
    if not isinstance(scenarios, dict):
        msg = "Missing execScenarios object"
        raise MissingK6ScenarioError(msg, suggestion="Ensure report includes execScenarios")

    scenario_config = scenarios.get(scenario_name)
    if not isinstance(scenario_config, dict):
        msg = f"Missing execScenarios entry for scenario: {scenario_name}"
        raise MissingK6ScenarioError(msg, suggestion="Ensure scenario name matches an execScenarios entry")
    return scenario_config


def _extract_env_name(tags: Any) -> str | None:
    """Extract optional environment name from scenario tags."""
    if not isinstance(tags, dict):
        return None

    tagged_env_name = tags.get("env_name")
    return tagged_env_name if isinstance(tagged_env_name, str) and tagged_env_name else None


def _test_run_duration_ms(*, source_payload: dict[str, Any]) -> float:
    """Return test run duration with a deterministic zero fallback."""
    state = source_payload.get("state")
    if isinstance(state, dict):
        duration = state.get("testRunDurationMs")
        if isinstance(duration, int | float) and not isinstance(duration, bool):
            return float(duration)

    duration = source_payload.get("testRunDurationMs")
    if isinstance(duration, int | float) and not isinstance(duration, bool):
        return float(duration)
    return 0.0


def _normalized_thresholds(*, source_payload: dict[str, Any]) -> dict[str, list[str]]:
    """Return normalized threshold definitions from a source payload."""
    threshold_payload = source_payload.get("thresholds")
    if not isinstance(threshold_payload, dict):
        threshold_payload = source_payload.get("execThresholds")
    if not isinstance(threshold_payload, dict):
        return {}

    return {
        metric_key: [expression for expression in expressions if isinstance(expression, str)]
        for metric_key, expressions in threshold_payload.items()
        if isinstance(metric_key, str) and isinstance(expressions, list)
    }


def _normalized_metrics(*, source_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return normalized metric payloads from a source payload."""
    metrics_payload = source_payload.get("metrics")
    if not isinstance(metrics_payload, dict):
        return {}

    return deepcopy(
        {
            metric_name: metric_payload
            for metric_name, metric_payload in metrics_payload.items()
            if isinstance(metric_name, str) and isinstance(metric_payload, dict)
        }
    )


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
