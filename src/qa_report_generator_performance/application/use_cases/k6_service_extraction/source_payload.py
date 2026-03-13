"""Application helpers for interpreting raw k6 source payload structures."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from qa_report_generator_performance.domain.exceptions import MissingK6ScenarioError

if TYPE_CHECKING:
    from qa_report_generator_performance.domain.analytics import K6Status


def pick_scenario_config(*, source_payload: dict[str, Any], scenario_name: str) -> dict[str, Any]:
    """Return the selected scenario config from ``execScenarios``."""
    scenarios = source_payload.get("execScenarios")
    if not isinstance(scenarios, dict):
        msg = "Missing execScenarios object"
        raise MissingK6ScenarioError(msg, suggestion="Ensure report includes execScenarios")

    scenario_config = scenarios.get(scenario_name)
    if not isinstance(scenario_config, dict):
        msg = f"Missing execScenarios entry for scenario: {scenario_name}"
        raise MissingK6ScenarioError(msg, suggestion="Ensure scenario name matches an execScenarios entry")
    return scenario_config


def extract_env_name(*, scenario_config: dict[str, Any]) -> str | None:
    """Extract the optional environment name from scenario tags."""
    tags = scenario_config.get("tags")
    if not isinstance(tags, dict):
        return None

    tagged_env_name = tags.get("env_name")
    return tagged_env_name if isinstance(tagged_env_name, str) and tagged_env_name else None


def pick_test_run_duration_ms(*, source_payload: dict[str, Any]) -> float:
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


def normalize_threshold_definitions(value: Any) -> dict[str, tuple[str, ...]]:
    """Normalize threshold definitions into a string-tuple mapping."""
    if not isinstance(value, dict):
        return {}

    normalized: dict[str, tuple[str, ...]] = {}
    for metric_key, expressions in value.items():
        if not isinstance(metric_key, str) or not isinstance(expressions, list):
            continue
        normalized[metric_key] = tuple(expression for expression in expressions if isinstance(expression, str))
    return normalized


def normalize_threshold_definitions_from_source_payload(*, source_payload: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    """Return normalized threshold definitions from a source payload."""
    threshold_payload = source_payload.get("thresholds")
    if not isinstance(threshold_payload, dict):
        threshold_payload = source_payload.get("execThresholds")
    return normalize_threshold_definitions(threshold_payload)


def normalize_metric_payloads_copy(*, source_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return a deep-copied metric mapping with only object payloads kept."""
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


def collect_threshold_statuses(*, metric_payloads: dict[str, Any]) -> dict[tuple[str, str], K6Status]:
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


def collect_threshold_status_map(*, metric_payloads: dict[str, Any]) -> dict[str, dict[str, bool]]:
    """Collect raw threshold ok-status values by metric and expression."""
    statuses: dict[str, dict[str, bool]] = {}
    for metric_key, metric_payload in metric_payloads.items():
        if not isinstance(metric_key, str) or not isinstance(metric_payload, dict):
            continue
        thresholds = metric_payload.get("thresholds")
        if not isinstance(thresholds, dict):
            continue
        for expression, evaluation in thresholds.items():
            if not isinstance(expression, str):
                continue
            if isinstance(evaluation, dict) and isinstance(evaluation.get("ok"), bool):
                statuses.setdefault(metric_key, {})[expression] = evaluation["ok"]
    return statuses
