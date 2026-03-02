"""Unit tests for k6 service extraction use case."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from qa_report_generator.application.use_cases.k6_service_extraction import K6ServiceExtractionService
from qa_report_generator.domain.exceptions import ExtractionVerificationError

if TYPE_CHECKING:
    from pathlib import Path


class StubStructuredLlm:
    """Stub deterministic LLM port for extraction tests."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        """Store planned JSON responses."""
        self._responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return the next planned response."""
        self.calls.append((system_prompt, user_prompt))
        return self._responses.pop(0)


def _source_payload() -> dict[str, Any]:
    return {
        "testRunDurationMs": 60000,
        "setup_data": {"large": "payload"},
        "root_group": {"ignored": True},
        "execScenarios": {
            "megatron-load": {
                "env_name": "staging",
                "executor": "constant-arrival-rate",
                "rate": 10,
                "duration": "1m",
                "preAllocatedVUs": 10,
                "maxVUs": 20,
            }
        },
        "metrics": {
            "checks": {"values": {"rate": 1.0, "passes": 100, "fails": 0}},
            "http_req_duration{test_name:megatron-load}": {
                "values": {
                    "min": 100.0,
                    "avg": 200.0,
                    "med": 150.0,
                    "max": 900.0,
                    "p(95)": 400.0,
                    "p(99)": 700.0,
                }
            },
            "http_req_failed": {"values": {"rate": 0.0, "passes": 100, "fails": 0}},
            "http_reqs": {"values": {"count": 100, "rate": 10.0}},
            "iterations": {"values": {"count": 100, "rate": 10.0}},
            "dropped_iterations": {"values": {"count": 0, "rate": 0.0}},
        },
        "thresholds": {"http_req_duration": ["p(95)<1000"]},
    }


def _extracted_payload() -> dict[str, Any]:
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
            "preAllocatedVUs": 10,
            "maxVUs": 20,
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


def test_extract_filters_removed_keys_and_returns_validated_payload(tmp_path: Path) -> None:
    """Extraction filters heavy keys and returns validated payload."""
    report_path_1 = tmp_path / "report-1.json"
    report_path_2 = tmp_path / "report-2.json"
    report_path_1.write_text(json.dumps(_source_payload()), encoding="utf-8")
    report_path_2.write_text(json.dumps(_source_payload()), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            _extracted_payload(),
            {"mismatches": []},
            _extracted_payload(),
            {"mismatches": []},
        ]
    )
    service = K6ServiceExtractionService(llm=llm)

    result = service.extract(
        service="megatron",
        report_paths=[report_path_1, report_path_2],
    )

    assert result.service == "megatron"
    assert len(result.extracted_runs) == 2
    assert result.extracted_runs[0].extracted["service"] == "megatron"
    assert result.extracted_runs[1].extracted["service"] == "megatron"
    extraction_prompt = json.loads(llm.calls[0][1])
    assert "setup_data" not in extraction_prompt["source"]
    assert "root_group" not in extraction_prompt["source"]


def test_extract_fails_on_verification_mismatch(tmp_path: Path) -> None:
    """Extraction fails strictly when verification returns mismatches."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_source_payload()), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            _extracted_payload(),
            {
                "mismatches": [
                    {
                        "field": "http_reqs.count",
                        "expected": "100",
                        "actual": "101",
                        "source_jsonpath": "$.metrics.http_reqs.values.count",
                        "extracted_jsonpath": "$.http_reqs.count",
                        "reason": "value mismatch",
                    }
                ]
            },
        ]
    )
    service = K6ServiceExtractionService(llm=llm)

    with pytest.raises(ExtractionVerificationError):
        service.extract(
            service="megatron",
            report_paths=[report_path],
        )
