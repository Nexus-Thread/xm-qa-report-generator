"""Unit tests for domain analytics models."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario


def test_k6_scenario_preserves_normalized_and_raw_fields() -> None:
    """K6Scenario stores normalized values alongside raw payload."""
    raw_payload = {"metrics": {"http_req_duration": {"values": {"avg": 123.4}}}}

    scenario = K6Scenario(
        source_report_file="megatron-1.json",
        name="megatron-load",
        env_name="perf",
        executor="constant-arrival-rate",
        rate=5.0,
        duration="1m",
        pre_allocated_vus=10,
        max_vus=20,
        test_run_duration_ms=60_000.0,
        thresholds={"http_req_duration": ["p(95)<500"]},
        metrics={"http_req_duration": {"values": {"avg": 123.4}}},
        raw_payload=raw_payload,
    )

    assert scenario.source_report_file == "megatron-1.json"
    assert scenario.name == "megatron-load"
    assert scenario.metrics["http_req_duration"]["values"]["avg"] == 123.4
    assert scenario.raw_payload is raw_payload


def test_k6_models_are_immutable_domain_records() -> None:
    """Domain analytics models reject field reassignment."""
    scenario = K6Scenario(
        source_report_file="megatron-1.json",
        name="megatron-load",
        env_name=None,
        executor="constant-arrival-rate",
        rate=5.0,
        duration="1m",
        pre_allocated_vus=10,
        max_vus=20,
        test_run_duration_ms=60_000.0,
        thresholds={},
        metrics={},
        raw_payload={},
    )
    parsed_report = K6ParsedReport(service="megatron", scenarios=[scenario])
    mutable_report = cast("Any", parsed_report)

    with pytest.raises(FrozenInstanceError):
        mutable_report.service = "other-service"
