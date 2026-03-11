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
    source_payload: dict[str, Any],
    source_report_file: str,
) -> list[K6Scenario]:
    """Build domain scenarios from a validated report payload."""
    if not report.exec_scenarios:
        msg = "Missing execScenarios object"
        raise ConfigurationError(msg, suggestion="Ensure report includes execScenarios")

    return [
        K6Scenario(
            source_report_file=source_report_file,
            name=scenario_name,
            source_payload=deepcopy(source_payload),
        )
        for scenario_name in report.exec_scenarios
    ]
