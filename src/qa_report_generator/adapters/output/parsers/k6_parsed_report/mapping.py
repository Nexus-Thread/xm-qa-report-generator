"""Mapping utilities from validated k6 payloads to domain scenarios."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from qa_report_generator.domain.analytics import K6Scenario
from qa_report_generator.domain.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pathlib import Path

    from .raw_schema import K6RawSummary


def remove_top_level_keys(source: dict[str, Any], *, remove_keys: frozenset[str]) -> dict[str, Any]:
    """Return payload copy with selected top-level keys removed."""
    if not remove_keys:
        return dict(source)
    return {key: value for key, value in source.items() if key not in remove_keys}


def normalize_metrics(value: Any) -> dict[str, dict[str, Any]]:
    """Normalize metrics payload to a dict of dict entries."""
    if not isinstance(value, dict):
        return {}
    return {metric_name: metric_payload for metric_name, metric_payload in value.items() if isinstance(metric_name, str) and isinstance(metric_payload, dict)}


def extract_env_name(*, tags: dict[str, Any]) -> str | None:
    """Extract optional environment name from scenario tags."""
    tagged_env_name = tags.get("env_name")
    if isinstance(tagged_env_name, str) and tagged_env_name:
        return tagged_env_name

    return None


def extract_scenarios(
    *,
    sanitized_source: dict[str, Any],
    validated_report: K6RawSummary,
    source_report_file: Path,
) -> list[K6Scenario]:
    """Build domain scenarios from a validated report payload."""
    exec_scenarios = validated_report.exec_scenarios
    if not exec_scenarios:
        msg = "Missing execScenarios object"
        raise ConfigurationError(msg, suggestion="Ensure report includes execScenarios")

    metrics = normalize_metrics(sanitized_source.get("metrics"))
    thresholds = validated_report.exec_thresholds
    run_duration = validated_report.state.test_run_duration_ms if validated_report.state else 0.0

    parsed_scenarios: list[K6Scenario] = []
    for scenario_name, raw_config in exec_scenarios.items():
        tags = raw_config.tags if isinstance(raw_config.tags, dict) else {}

        parsed_scenarios.append(
            K6Scenario(
                source_report_file=source_report_file.name,
                name=str(scenario_name),
                env_name=extract_env_name(tags=tags),
                executor=raw_config.executor,
                rate=raw_config.rate if raw_config.rate is not None else 0.0,
                duration=raw_config.duration if raw_config.duration is not None else "",
                pre_allocated_vus=(raw_config.pre_allocated_vus if raw_config.pre_allocated_vus is not None else 0),
                max_vus=raw_config.max_vus if raw_config.max_vus is not None else 0,
                test_run_duration_ms=run_duration,
                thresholds=deepcopy(thresholds),
                metrics=deepcopy(metrics),
                raw_payload=deepcopy(sanitized_source),
            )
        )

    return parsed_scenarios
