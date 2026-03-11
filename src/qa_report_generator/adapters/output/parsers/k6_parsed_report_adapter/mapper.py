"""Mapping utilities from validated k6 payloads to domain scenarios."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

from qa_report_generator.domain.analytics import K6Scenario
from qa_report_generator.domain.exceptions import ConfigurationError

if TYPE_CHECKING:
    from .schema import K6RawSummary


def build_scenarios(
    *,
    report: K6RawSummary,
    raw_payload: dict[str, Any],
    source_report_file: str,
) -> list[K6Scenario]:
    """Build domain scenarios from a validated report payload."""
    if not report.exec_scenarios:
        msg = "Missing execScenarios object"
        raise ConfigurationError(msg, suggestion="Ensure report includes execScenarios")

    run_duration = report.state.test_run_duration_ms if report.state is not None else 0.0

    return [
        K6Scenario(
            source_report_file=source_report_file,
            name=scenario_name,
            env_name=_extract_env_name(raw_config.tags),
            executor=raw_config.executor,
            rate=raw_config.rate if raw_config.rate is not None else 0.0,
            duration=raw_config.duration if raw_config.duration is not None else "",
            pre_allocated_vus=(raw_config.pre_allocated_vus if raw_config.pre_allocated_vus is not None else 0),
            max_vus=raw_config.max_vus if raw_config.max_vus is not None else 0,
            test_run_duration_ms=run_duration,
            thresholds=deepcopy(report.exec_thresholds),
            metrics=deepcopy(report.metrics),
            raw_payload=deepcopy(raw_payload),
        )
        for scenario_name, raw_config in report.exec_scenarios.items()
    ]


def _extract_env_name(tags: dict[str, Any] | None) -> str | None:
    """Extract optional environment name from scenario tags."""
    if tags is None:
        return None

    tagged_env_name = tags.get("env_name")
    if isinstance(tagged_env_name, str) and tagged_env_name:
        return tagged_env_name
    return None
