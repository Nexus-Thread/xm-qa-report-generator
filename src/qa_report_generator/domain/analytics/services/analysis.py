"""Domain services for scenario and overall k6 analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Sequence

from qa_report_generator.domain.analytics.models import (
    K6OverallAnalysis,
    K6ScenarioAnalysis,
    K6Status,
    K6ThresholdSummary,
)


def analyze_scenario_run(*, run_payload: dict[str, Any], source_report_files: Sequence[str]) -> K6ScenarioAnalysis:
    """Analyze one final run payload into scenario-level facts."""
    scenario = _as_dict(run_payload.get("scenario"))
    threshold_results = _build_threshold_summaries(run_payload=run_payload)
    status = _derive_scenario_status(threshold_results=threshold_results)
    scenario_name = _as_string(scenario.get("name")) or "unknown"
    failing_thresholds = tuple(f"{threshold.metric_key}:{threshold.expression}" for threshold in threshold_results if threshold.status == "fail")
    return K6ScenarioAnalysis(
        scenario_name=scenario_name,
        env_name=_as_string(scenario.get("env_name")),
        source_report_files=tuple(source_report_files),
        status=status,
        executor=_as_string(scenario.get("executor")),
        rate=_as_float(scenario.get("rate")),
        duration=_as_string(scenario.get("duration")),
        pre_allocated_vus=_as_int(scenario.get("preAllocatedVUs") or scenario.get("pre_allocated_vus")),
        max_vus=_as_int(scenario.get("maxVUs") or scenario.get("max_vus")),
        threshold_results=tuple(threshold_results),
        failing_thresholds=failing_thresholds,
    )


def analyze_overall_scenarios(*, scenario_analyses: Sequence[K6ScenarioAnalysis]) -> K6OverallAnalysis:
    """Aggregate scenario analyses into overall service-level facts."""
    total_scenarios = len(scenario_analyses)
    passed_scenarios = sum(1 for analysis in scenario_analyses if analysis.status == "pass")
    failed_scenarios = sum(1 for analysis in scenario_analyses if analysis.status == "fail")
    unknown_scenarios = sum(1 for analysis in scenario_analyses if analysis.status == "unknown")

    if failed_scenarios > 0:
        status: K6Status = "fail"
    elif unknown_scenarios > 0:
        status = "unknown"
    else:
        status = "pass"

    return K6OverallAnalysis(
        status=status,
        total_scenarios=total_scenarios,
        passed_scenarios=passed_scenarios,
        failed_scenarios=failed_scenarios,
        unknown_scenarios=unknown_scenarios,
        scenarios_requiring_attention=tuple(analysis.scenario_name for analysis in scenario_analyses if analysis.status != "pass"),
    )


def _build_threshold_summaries(*, run_payload: dict[str, Any]) -> list[K6ThresholdSummary]:
    """Build normalized threshold summaries from extracted payload fields."""
    prebuilt_threshold_results = run_payload.get("threshold_results")
    if isinstance(prebuilt_threshold_results, list):
        return _prebuilt_threshold_summaries(prebuilt_threshold_results)

    threshold_definitions = _normalize_threshold_definitions(run_payload.get("thresholds"))
    threshold_statuses = _collect_threshold_statuses(metric_payloads=run_payload)

    summaries: list[K6ThresholdSummary] = []
    for metric_key, expressions in sorted(threshold_definitions.items()):
        summaries.extend(
            K6ThresholdSummary(
                metric_key=metric_key,
                expression=expression,
                status=threshold_statuses.get((metric_key, expression), "unknown"),
            )
            for expression in expressions
        )
    return summaries


def _normalize_threshold_definitions(value: Any) -> dict[str, tuple[str, ...]]:
    """Normalize threshold definitions into a string-tuple mapping."""
    if not isinstance(value, dict):
        return {}

    normalized: dict[str, tuple[str, ...]] = {}
    for metric_key, expressions in value.items():
        if not isinstance(metric_key, str) or not isinstance(expressions, list):
            continue
        normalized[metric_key] = tuple(expression for expression in expressions if isinstance(expression, str))
    return normalized


def _collect_threshold_statuses(*, metric_payloads: dict[str, Any]) -> dict[tuple[str, str], K6Status]:
    """Collect threshold statuses from metric payloads when present."""
    statuses: dict[tuple[str, str], K6Status] = {}
    for metric_key, metric_payload in metric_payloads.items():
        if not isinstance(metric_payload, dict):
            continue
        thresholds = metric_payload.get("thresholds")
        if not isinstance(thresholds, dict):
            continue
        for expression, evaluation in thresholds.items():
            if not isinstance(expression, str):
                continue
            if isinstance(evaluation, dict) and isinstance(evaluation.get("ok"), bool):
                statuses[(metric_key, expression)] = "pass" if evaluation["ok"] else "fail"
    return statuses


def _prebuilt_threshold_summaries(value: list[Any]) -> list[K6ThresholdSummary]:
    """Convert prebuilt threshold summary payloads into domain records."""
    summaries: list[K6ThresholdSummary] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        metric_key = _as_string(item.get("metric_key"))
        expression = _as_string(item.get("expression"))
        status = item.get("status")
        if metric_key is None or expression is None or status not in {"pass", "fail", "unknown"}:
            continue
        summaries.append(
            K6ThresholdSummary(
                metric_key=metric_key,
                expression=expression,
                status=cast("K6Status", status),
            )
        )
    return summaries


def _derive_scenario_status(*, threshold_results: Sequence[K6ThresholdSummary]) -> K6Status:
    """Derive scenario pass/fail status from threshold results."""
    if not threshold_results:
        return "unknown"
    if any(result.status == "fail" for result in threshold_results):
        return "fail"
    if all(result.status == "pass" for result in threshold_results):
        return "pass"
    return "unknown"


def _as_dict(value: Any) -> dict[str, Any]:
    """Return a dict value or an empty dict fallback."""
    return cast("dict[str, Any]", value) if isinstance(value, dict) else {}


def _as_string(value: Any) -> str | None:
    """Return a non-empty string value when available."""
    return value if isinstance(value, str) and value else None


def _as_float(value: Any) -> float | None:
    """Return a numeric value as float when available."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return float(value)


def _as_int(value: Any) -> int | None:
    """Return an integer value when available."""
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value
