"""Unit tests for megatron extraction schema and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from qa_report_generator.application.service_definitions.megatron.schema import MegatronExtractedMetrics


def _valid_payload() -> dict[str, object]:
    return {
        "service": "megatron",
        "report_file": "report.json",
        "test_run_duration_ms": 60000,
        "scenario": {
            "name": "megatron-load",
            "env_name": "staging",
            "executor": "constant-arrival-rate",
            "rate": 10,
            "duration": "1m",
            "pre_allocated_vus": 10,
            "max_vus": 20,
        },
        "checks": {"rate": 1.0, "passes": 100, "fails": 0},
        "http_req_duration": {
            "min": 100.0,
            "avg": 200.0,
            "med": 150.0,
            "max": 900.0,
            "p(95)": 400.0,
            "p(99)": 700.0,
        },
        "http_req_failed": {"rate": 0.0, "passes": 100, "fails": 0},
        "http_reqs": {"count": 100, "rate": 10.0},
        "iterations": {"count": 100, "rate": 10.0},
        "dropped_iterations": {"count": 0, "rate": 0.0},
        "thresholds": {"http_req_duration": ["p(95)<1000"]},
    }


def test_megatron_schema_accepts_valid_payload() -> None:
    """Megatron schema validates an expected extracted payload."""
    model = MegatronExtractedMetrics.model_validate(_valid_payload())

    assert model.service == "megatron"
    assert model.http_req_duration.p95 == 400.0


def test_megatron_schema_rejects_unknown_fields() -> None:
    """Megatron schema forbids extra keys in strict extraction output."""
    payload = _valid_payload()
    payload["unexpected"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        MegatronExtractedMetrics.model_validate(payload)


def test_megatron_schema_accepts_camel_case_scenario_aliases() -> None:
    """Megatron schema accepts canonical k6 scenario alias field names."""
    payload = _valid_payload()
    payload["scenario"] = {
        "name": "megatron-load",
        "env_name": "staging",
        "executor": "constant-arrival-rate",
        "rate": 10,
        "duration": "1m",
        "preAllocatedVUs": 10,
        "maxVUs": 20,
    }

    model = MegatronExtractedMetrics.model_validate(payload)

    assert model.scenario.pre_allocated_vus == 10
    assert model.scenario.max_vus == 20


def test_megatron_schema_rejects_invalid_scenario_bounds() -> None:
    """Megatron schema rejects scenario with max vus lower than preallocated."""
    payload = _valid_payload()
    payload["scenario"] = {
        "name": "megatron-load",
        "env_name": "staging",
        "executor": "constant-arrival-rate",
        "rate": 10,
        "duration": "1m",
        "pre_allocated_vus": 20,
        "max_vus": 10,
    }
    with pytest.raises(ValueError, match="maxVUs must be >= preAllocatedVUs"):
        MegatronExtractedMetrics.model_validate(payload)


def test_megatron_schema_exposes_shared_ai_descriptions() -> None:
    """Megatron schema includes reusable field descriptions for AI extraction."""
    schema = MegatronExtractedMetrics.model_json_schema()
    properties = schema["properties"]

    assert properties["service"]["description"] == "Use literal service name 'megatron'"
    assert properties["report_file"]["description"] == "Use verification_context.report_file, populated from the selected scenario source report filename"
    assert properties["test_run_duration_ms"]["description"] == "Use $.state.testRunDurationMs"
    assert properties["scenario"]["description"] == "Use the selected scenario from $.execScenarios"
    assert properties["checks"]["description"] == "Use $.metrics.checks.values"
    assert (
        properties["http_req_duration"]["description"]
        == "Use scenario-tagged $.metrics.http_req_duration{test_name:<scenario>}.values when present, otherwise use $.metrics.http_req_duration.values"
    )
    assert properties["dropped_iterations"]["description"] == "Use $.metrics.dropped_iterations.values when present; otherwise use null"
    assert properties["thresholds"]["description"] == "Use $.execThresholds"
