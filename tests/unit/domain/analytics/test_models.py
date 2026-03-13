"""Unit tests for domain analytics models."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from typing import Any, cast

import pytest

from qa_report_generator_performance.domain.analytics import K6ParsedReport, K6Scenario


def test_k6_scenario_keeps_only_minimal_stored_fields() -> None:
    """K6Scenario exposes only the minimal stored source-of-truth fields."""
    source_payload = {
        "testRunDurationMs": 60_000.0,
        "execScenarios": {
            "other-load": {
                "tags": {"env_name": "dev"},
                "executor": "shared-iterations",
                "rate": 1,
                "duration": "30s",
                "preAllocatedVUs": 1,
                "maxVUs": 2,
            },
            "megatron-load": {
                "tags": {"env_name": "perf"},
                "executor": "constant-arrival-rate",
                "rate": 5,
                "duration": "1m",
                "preAllocatedVUs": 10,
                "maxVUs": 20,
            },
        },
        "execThresholds": {"http_req_duration{test_name:megatron-load}": ["p(95)<300"]},
        "metrics": {
            "http_req_duration": {"values": {"avg": 123.4}},
            "invalid_metric": 10,
        },
    }

    scenario = K6Scenario(
        source_report_file="megatron-1.json",
        name="megatron-load",
        source_payload=source_payload,
    )

    assert [field.name for field in fields(K6Scenario)] == [
        "source_report_file",
        "name",
        "source_payload",
    ]
    assert scenario.source_report_file == "megatron-1.json"
    assert scenario.name == "megatron-load"
    assert scenario.source_payload["metrics"]["http_req_duration"]["values"]["avg"] == 123.4
    assert scenario.source_payload is source_payload


def test_k6_models_are_immutable_domain_records() -> None:
    """Domain analytics models reject field reassignment."""
    scenario = K6Scenario(
        source_report_file="megatron-1.json",
        name="megatron-load",
        source_payload={
            "testRunDurationMs": 60_000.0,
            "execScenarios": {
                "megatron-load": {
                    "executor": "constant-arrival-rate",
                    "rate": 5,
                    "duration": "1m",
                    "preAllocatedVUs": 10,
                    "maxVUs": 20,
                }
            },
        },
    )
    parsed_report = K6ParsedReport(service="megatron", scenarios=(scenario,))
    mutable_report = cast("Any", parsed_report)

    with pytest.raises(FrozenInstanceError):
        mutable_report.service = "other-service"
