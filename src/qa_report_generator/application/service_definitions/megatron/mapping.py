"""Backward-compatible exports for k6 metric selection helpers."""

from __future__ import annotations

from qa_report_generator.domain.analytics.k6_metrics import (
    SCENARIO_KEY_JSONPATH,
    pick_metric,
    pick_primary_scenario_name,
    scenario_metric_key,
)

__all__ = [
    "SCENARIO_KEY_JSONPATH",
    "pick_metric",
    "pick_primary_scenario_name",
    "scenario_metric_key",
]
