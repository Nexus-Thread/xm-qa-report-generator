"""Unit tests for k6 service extraction use case."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import pytest

from qa_report_generator.application.use_cases.k6_service_extraction import K6ServiceExtractionService
from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario
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


class StubK6ParsedReportParser:
    """Stub parser returning a deterministic parsed report."""

    def __init__(self, parsed_report: K6ParsedReport) -> None:
        """Store parsed report template to return for parse calls."""
        self._parsed_report = parsed_report

    def parse(
        self,
        *,
        service: str,
        report_files: list[Path],
        remove_keys: frozenset[str] | None = None,
    ) -> K6ParsedReport:
        """Return parsed report with one scenario entry per report file."""
        del remove_keys
        template = self._parsed_report.scenarios[0]
        scenarios = [
            K6Scenario(
                source_report_file=report_file.name,
                name=template.name,
                env_name=template.env_name,
                executor=template.executor,
                rate=template.rate,
                duration=template.duration,
                pre_allocated_vus=template.pre_allocated_vus,
                max_vus=template.max_vus,
                test_run_duration_ms=template.test_run_duration_ms,
                thresholds=deepcopy(template.thresholds),
                metrics=deepcopy(template.metrics),
                raw_payload=deepcopy(template.raw_payload),
            )
            for report_file in report_files
        ]
        return K6ParsedReport(service=service, scenarios=scenarios)


def _source_payload() -> dict[str, Any]:
    return {
        "testRunDurationMs": 60000,
        "env": None,
        "setup_data": {"large": "payload"},
        "root_group": {"ignored": True},
        "execScenarios": {
            "megatron-load": {
                "env_name": None,
                "tags": {"env_name": "staging"},
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


def _parsed_report(*, service: str = "megatron", source_report_file: str = "report.json") -> K6ParsedReport:
    """Build parsed report fixture for service extraction tests."""
    return _parsed_report_with_source_payload(
        source_payload=_source_payload(),
        service=service,
        source_report_file=source_report_file,
    )


def _parsed_report_with_source_payload(
    *,
    source_payload: dict[str, Any],
    service: str = "megatron",
    source_report_file: str = "report.json",
) -> K6ParsedReport:
    """Build parsed report fixture from a provided source payload."""
    scenario_payload = _source_payload()
    scenario_payload = deepcopy(source_payload)
    scenario_payload.pop("setup_data", None)
    scenario_payload.pop("root_group", None)

    return K6ParsedReport(
        service=service,
        scenarios=[
            K6Scenario(
                source_report_file=source_report_file,
                name="megatron-load",
                env_name="staging",
                executor="constant-arrival-rate",
                rate=10.0,
                duration="1m",
                pre_allocated_vus=10,
                max_vus=20,
                test_run_duration_ms=60000.0,
                thresholds={"http_req_duration": ["p(95)<1000"]},
                metrics=scenario_payload["metrics"],
                raw_payload=scenario_payload,
            )
        ],
    )


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
    parser = StubK6ParsedReportParser(_parsed_report())
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(
        service="megatron",
        report_paths=[report_path_1, report_path_2],
    )

    assert result.service == "megatron"
    assert result.mode == "service_specific"
    assert len(result.extracted_runs) == 2
    assert result.extracted_runs[0].extracted["service"] == "megatron"
    assert result.extracted_runs[1].extracted["service"] == "megatron"
    assert llm.calls[0][0].startswith("You extract structured k6 metrics from a filtered k6 JSON report.")
    assert "Return only a JSON object that matches the provided schema." in llm.calls[0][0]
    extraction_prompt = json.loads(llm.calls[0][1])
    assert extraction_prompt["task"] == "extract_k6_metrics"
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
    parser = StubK6ParsedReportParser(_parsed_report())
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    with pytest.raises(ExtractionVerificationError):
        service.extract(
            service="megatron",
            report_paths=[report_path],
        )


def test_verification_prompt_includes_leaf_metric_mapping_rules(tmp_path: Path) -> None:
    """Verification prompt enforces leaf-value metric comparisons."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_source_payload()), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            _extracted_payload(),
            {"mismatches": []},
        ]
    )
    parser = StubK6ParsedReportParser(_parsed_report())
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    service.extract(
        service="megatron",
        report_paths=[report_path],
    )

    assert llm.calls[1][0].startswith("You verify extracted k6 metrics against the source JSON.")
    assert '{"mismatches": []}' in llm.calls[1][0]
    verification_prompt_payload = json.loads(llm.calls[1][1])
    assert verification_prompt_payload["task"] == "verify_k6_extraction"
    assert "target_schema" in verification_prompt_payload
    rules = verification_prompt_payload["rules"]
    assert any("Treat missing required fields as mismatches" in rule for rule in rules)
    assert any("allows null for a field" in rule for rule in rules)
    assert any("optional metric object is absent in source and the extracted value is null" in rule for rule in rules)
    assert any("source of truth" in rule for rule in rules)
    assert any("multiple candidate source values" in rule for rule in rules)
    assert any("unrelated duplicate source fields" in rule for rule in rules)
    assert any("selected scenario entry" in rule for rule in rules)
    assert any("exact source and extracted JSONPath" in rule for rule in rules)
    assert any("never to whole metric objects" in rule for rule in rules)
    assert any("Do not infer, normalize, or reinterpret values" in rule for rule in rules)


def test_verification_prompt_includes_schema_guidance_for_duplicate_values(tmp_path: Path) -> None:
    """Verification payload includes schema guidance for ambiguous source fields."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_source_payload()), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            _extracted_payload(),
            {"mismatches": []},
        ]
    )
    parser = StubK6ParsedReportParser(_parsed_report())
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    service.extract(
        service="megatron",
        report_paths=[report_path],
    )

    verification_prompt_payload = json.loads(llm.calls[1][1])
    scenario_properties = verification_prompt_payload["target_schema"]["$defs"]["Scenario"]["properties"]
    assert verification_prompt_payload["source"]["env"] is None
    assert verification_prompt_payload["source"]["execScenarios"]["megatron-load"]["tags"]["env_name"] == "staging"
    assert scenario_properties["env_name"]["description"] == "Use $.execScenarios.<scenario>.tags.env_name"


def test_verification_prompt_describes_optional_missing_metric_as_null(tmp_path: Path) -> None:
    """Verification payload explains that absent optional metrics should validate as null."""
    report_path = tmp_path / "report.json"
    source_payload = _source_payload()
    source_payload["metrics"].pop("dropped_iterations", None)
    report_path.write_text(json.dumps(source_payload), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            {**_extracted_payload(), "dropped_iterations": None},
            {"mismatches": []},
        ]
    )
    parser = StubK6ParsedReportParser(_parsed_report_with_source_payload(source_payload=source_payload))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    service.extract(
        service="megatron",
        report_paths=[report_path],
    )

    verification_prompt_payload = json.loads(llm.calls[1][1])
    dropped_iterations_schema = verification_prompt_payload["target_schema"]["properties"]["dropped_iterations"]
    rules = verification_prompt_payload["rules"]

    assert "otherwise use null" in dropped_iterations_schema["description"]
    assert verification_prompt_payload["source"]["metrics"].get("dropped_iterations") is None
    assert verification_prompt_payload["extracted"]["dropped_iterations"] is None
    assert any("allows null for a field" in rule for rule in rules)
    assert any("optional metric object is absent in source and the extracted value is null" in rule for rule in rules)


def test_extract_returns_generic_payload_when_service_definition_is_missing(tmp_path: Path) -> None:
    """Extraction returns generic parsed payload when no service definition exists."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_source_payload()), encoding="utf-8")

    llm = StubStructuredLlm([])
    parser = StubK6ParsedReportParser(_parsed_report(service="unknown-service", source_report_file="report.json"))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(
        service="unknown-service",
        report_paths=[report_path],
    )

    assert result.service == "unknown-service"
    assert result.mode == "generic"
    assert len(result.extracted_runs) == 1
    assert result.extracted_runs[0].extracted["scenario"]["name"] == "megatron-load"
    assert llm.calls == []
