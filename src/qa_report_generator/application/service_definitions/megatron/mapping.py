"""Mapping helpers for megatron-specific k6 metrics."""

from __future__ import annotations

from typing import Any

SCENARIO_KEY_JSONPATH = "$.execScenarios"


def pick_primary_scenario_name(source: dict[str, Any]) -> str:
    """Pick the single scenario key from execScenarios."""
    scenarios = source.get("execScenarios", {})
    if not isinstance(scenarios, dict) or not scenarios:
        msg = "Missing execScenarios object"
        raise ValueError(msg)
    return next(iter(scenarios.keys()))


def scenario_metric_key(metric_prefix: str, scenario_name: str) -> str:
    """Build scenario-tagged metric key."""
    return f"{metric_prefix}{{test_name:{scenario_name}}}"


def pick_metric(source: dict[str, Any], metric_prefix: str, scenario_name: str) -> dict[str, Any]:
    """Pick scenario-specific metric when available, else generic one."""
    metrics = source.get("metrics", {})
    if not isinstance(metrics, dict):
        msg = "Missing metrics object"
        raise TypeError(msg)

    scenario_key = scenario_metric_key(metric_prefix, scenario_name)
    if scenario_key in metrics and isinstance(metrics[scenario_key], dict):
        return metrics[scenario_key]
    metric = metrics.get(metric_prefix)
    if isinstance(metric, dict):
        return metric
    msg = f"Missing metric: {metric_prefix}"
    raise ValueError(msg)
