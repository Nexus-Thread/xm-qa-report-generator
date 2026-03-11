"""Unit tests for raw k6 metric selection helpers."""

from __future__ import annotations

from typing import Any

import pytest

from qa_report_generator.application.use_cases.k6_service_extraction.metric_selection import (
    pick_metric,
    pick_primary_scenario_name,
    scenario_metric_key,
)
from qa_report_generator.domain.exceptions import (
    InvalidK6MetricPayloadError,
    MissingK6MetricError,
    MissingK6ScenarioError,
)


def test_pick_primary_scenario_name_returns_only_scenario_key() -> None:
    """Primary scenario helper returns the first scenario key."""
    source: dict[str, Any] = {"execScenarios": {"megatron-load": {}}}

    result = pick_primary_scenario_name(source)

    assert result == "megatron-load"


def test_pick_primary_scenario_name_raises_domain_error_when_missing() -> None:
    """Primary scenario helper raises domain error for missing scenarios."""
    with pytest.raises(MissingK6ScenarioError):
        pick_primary_scenario_name({})


def test_scenario_metric_key_builds_tagged_metric_name() -> None:
    """Scenario metric key helper formats tagged metric names."""
    assert scenario_metric_key("http_req_duration", "megatron-load") == "http_req_duration{test_name:megatron-load}"


def test_pick_metric_prefers_scenario_specific_metric() -> None:
    """Metric helper prefers scenario-specific metric when present."""
    source: dict[str, Any] = {
        "metrics": {
            "http_req_duration": {"values": {"avg": 999.0}},
            "http_req_duration{test_name:megatron-load}": {"values": {"avg": 200.0}},
        }
    }

    result = pick_metric(source, "http_req_duration", "megatron-load")

    assert result == {"values": {"avg": 200.0}}


def test_pick_metric_falls_back_to_generic_metric() -> None:
    """Metric helper falls back to generic metric when tagged one is absent."""
    source: dict[str, Any] = {"metrics": {"http_req_duration": {"values": {"avg": 200.0}}}}

    result = pick_metric(source, "http_req_duration", "megatron-load")

    assert result == {"values": {"avg": 200.0}}


def test_pick_metric_raises_domain_error_for_invalid_metrics_shape() -> None:
    """Metric helper raises domain error when metrics object is invalid."""
    with pytest.raises(InvalidK6MetricPayloadError):
        pick_metric({"metrics": []}, "http_req_duration", "megatron-load")


def test_pick_metric_raises_domain_error_for_missing_metric() -> None:
    """Metric helper raises domain error when required metric is missing."""
    with pytest.raises(MissingK6MetricError):
        pick_metric({"metrics": {}}, "http_req_duration", "megatron-load")
