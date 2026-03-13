"""Application helpers for selecting scenario-specific metrics from raw k6 payloads."""

from __future__ import annotations

from typing import Any

from qa_report_generator_performance.domain.exceptions import (
    InvalidK6MetricPayloadError,
    MissingK6MetricError,
    MissingK6ScenarioError,
)


def pick_primary_scenario_name(source: dict[str, Any]) -> str:
    """Pick the single scenario key from ``execScenarios``."""
    scenarios = source.get("execScenarios", {})
    if not isinstance(scenarios, dict) or not scenarios:
        msg = "Missing execScenarios object"
        raise MissingK6ScenarioError(msg, suggestion="Ensure report includes execScenarios")
    return next(iter(scenarios.keys()))


def scenario_metric_key(metric_prefix: str, scenario_name: str) -> str:
    """Build a scenario-tagged metric key."""
    return f"{metric_prefix}{{test_name:{scenario_name}}}"


def pick_metric(source: dict[str, Any], metric_prefix: str, scenario_name: str) -> dict[str, Any]:
    """Pick scenario-specific metric when available, else generic one."""
    metrics = source.get("metrics", {})
    if not isinstance(metrics, dict):
        msg = "Missing metrics object"
        raise InvalidK6MetricPayloadError(msg, suggestion="Ensure report includes a metrics object")

    tagged_metric_key = scenario_metric_key(metric_prefix, scenario_name)
    if tagged_metric_key in metrics and isinstance(metrics[tagged_metric_key], dict):
        return metrics[tagged_metric_key]

    metric = metrics.get(metric_prefix)
    if isinstance(metric, dict):
        return metric

    msg = f"Missing metric: {metric_prefix}"
    raise MissingK6MetricError(msg, suggestion="Ensure report includes the required metric")
