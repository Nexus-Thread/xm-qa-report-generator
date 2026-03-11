"""Unit tests for k6 service extraction use case."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import TYPE_CHECKING, Any

import pytest

from qa_report_generator.application.use_cases.k6_service_extraction import (
    K6ServiceExtractionDebugConfig,
    K6ServiceExtractionService,
)
from qa_report_generator.application.use_cases.k6_service_extraction.verification import parse_mismatches
from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario
from qa_report_generator.domain.exceptions import ExtractionVerificationError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


class SpyDebugJsonWriter:
    """Spy writer for model snapshot persistence."""

    def __init__(self) -> None:
        """Store write calls."""
        self.calls: list[tuple[str, object]] = []

    def write_json(self, *, label: str, payload: object) -> Path:
        """Record one model snapshot write call."""
        from pathlib import Path as _Path

        self.calls.append((label, payload))
        return _Path(f"out/test-debug/{label}.json")


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
        report_files: Sequence[Path],
        remove_keys: frozenset[str] = frozenset(),
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
            "http_req_blocked": {"values": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9}},
            "http_req_connecting": {"values": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9}},
            "http_req_receiving": {"values": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9}},
            "http_req_sending": {"values": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9}},
            "http_req_tls_handshaking": {"values": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9}},
            "http_req_waiting": {"values": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9}},
            "iteration_duration": {"values": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9}},
            "http_req_failed": {"values": {"rate": 0.0, "passes": 100, "fails": 0}},
            "http_reqs": {"values": {"count": 100, "rate": 10.0}},
            "iterations": {"values": {"count": 100, "rate": 10.0}},
            "data_received": {"values": {"count": 1000, "rate": 100.0}},
            "data_sent": {"values": {"count": 500, "rate": 50.0}},
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
        "http_req_blocked": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_connecting": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_receiving": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_sending": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_tls_handshaking": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_waiting": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "iteration_duration": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_failed": {"rate": 0.0, "passes": 100, "fails": 0},
        "http_reqs": {"count": 100, "rate": 10.0},
        "iterations": {"count": 100, "rate": 10.0},
        "data_received": {"count": 1000, "rate": 100.0},
        "data_sent": {"count": 500, "rate": 50.0},
        "dropped_iterations": {"count": 0, "rate": 0.0},
        "thresholds": {"http_req_duration": ["p(95)<1000"]},
    }


def _symbolstreeservice_extracted_payload(*, scenario_name: str, report_file: str) -> dict[str, Any]:
    """Build symbolstreeservice extraction payload for one numbered scenario."""
    return {
        "service": "symbolstreeservice",
        "report_file": report_file,
        "test_run_duration_ms": 60000,
        "scenario": {
            "name": scenario_name,
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
        "http_req_blocked": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_connecting": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_receiving": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_sending": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_tls_handshaking": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_waiting": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "iteration_duration": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_failed": {"rate": 0.0, "passes": 100, "fails": 0},
        "http_reqs": {"count": 100, "rate": 10.0},
        "iterations": {"count": 100, "rate": 10.0},
        "data_received": {"count": 1000, "rate": 100.0},
        "data_sent": {"count": 500, "rate": 50.0},
        "dropped_iterations": {"count": 0, "rate": 0.0},
        "thresholds": {f"http_req_duration{{test_name:{scenario_name}}}": ["p(95)<1000"]},
    }


def _symbolstreeservice_passthrough_payload(*, report_file: str) -> dict[str, Any]:
    """Build symbolstreeservice extraction payload for the non-grouped scenario."""
    return {
        "service": "symbolstreeservice",
        "report_file": report_file,
        "test_run_duration_ms": 61000,
        "scenario": {
            "name": "getSymbolsTree",
            "env_name": "staging",
            "executor": "constant-arrival-rate",
            "rate": 11,
            "duration": "1m",
            "preAllocatedVUs": 11,
            "maxVUs": 21,
        },
        "checks": {"rate": 0.2, "passes": 80, "fails": 20},
        "http_req_duration": {
            "min": 5.0,
            "avg": 50.0,
            "med": 40.0,
            "max": 500.0,
            "p(95)": 450.0,
            "p(99)": 490.0,
        },
        "http_req_blocked": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_connecting": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_receiving": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_sending": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_tls_handshaking": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_waiting": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "iteration_duration": {"min": 1.0, "avg": 2.0, "med": 2.0, "max": 3.0, "p(95)": 2.5, "p(99)": 2.9},
        "http_req_failed": {"rate": 0.2, "passes": 80, "fails": 20},
        "http_reqs": {"count": 100, "rate": 10.0},
        "iterations": {"count": 100, "rate": 10.0},
        "data_received": {"count": 1000, "rate": 100.0},
        "data_sent": {"count": 500, "rate": 50.0},
        "dropped_iterations": {"count": 1, "rate": 0.1},
        "thresholds": {"http_req_duration{test_name:getSymbolsTree}": ["p(95)<1000"]},
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
    scenario_name = next(iter(source_payload["execScenarios"].keys()))

    return K6ParsedReport(
        service=service,
        scenarios=[
            K6Scenario(
                source_report_file=source_report_file,
                name=scenario_name,
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
    assert len(result.runs) == 2
    assert result.overall_summary.total_scenarios == 2
    assert len(result.scenario_summaries) == 2
    assert "report_file" not in result.runs[0].extracted
    assert "report_file" not in result.runs[1].extracted
    assert result.runs[0].extracted["threshold_results"] == [
        {
            "metric_key": "http_req_duration",
            "expression": "p(95)<1000",
            "status": "unknown",
        }
    ]
    assert result.runs[0].extracted["service"] == "megatron"
    assert result.runs[1].extracted["service"] == "megatron"
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
    assert verification_prompt_payload["verification_context"]["report_file"] == "report.json"
    rules = verification_prompt_payload["rules"]
    assert any("Treat missing required fields as mismatches" in rule for rule in rules)
    assert any("only when expected and actual differ" in rule for rule in rules)
    assert any("Do not include successful comparisons" in rule for rule in rules)
    assert any("If a field matches exactly, do not mention it" in rule for rule in rules)
    assert any("coming from verification_context" in rule for rule in rules)
    assert any("context-backed fields" in rule for rule in rules)
    assert any("allows null for a field" in rule for rule in rules)
    assert any("optional metric object is absent in source and the extracted value is null" in rule for rule in rules)
    assert any("source of truth" in rule for rule in rules)
    assert any("multiple candidate source values" in rule for rule in rules)
    assert any("never use an untagged sibling metric" in rule for rule in rules)
    assert any("exact test_name:<scenario> tagged metrics" in rule for rule in rules)
    assert any("unrelated tagged variants" in rule for rule in rules)
    assert any("reasoning and source_jsonpath consistent" in rule for rule in rules)
    assert any("reason says a tagged metric should be used" in rule for rule in rules)
    assert any("unrelated duplicate source fields" in rule for rule in rules)
    assert any("selected scenario entry" in rule for rule in rules)
    assert any("exact source and extracted JSONPath" in rule for rule in rules)
    assert any("never to whole metric objects" in rule for rule in rules)
    assert any("Do not infer, normalize, or reinterpret values" in rule for rule in rules)


def test_parse_mismatches_ignores_self_contradictory_tagged_metric_mismatch() -> None:
    """Contradictory tagged-metric mismatch reports are ignored as verifier errors."""
    mismatches = parse_mismatches(
        {
            "mismatches": [
                {
                    "field": "http_req_failed.fails",
                    "expected": 5970,
                    "actual": 3342,
                    "source_jsonpath": "$.source.metrics.http_req_failed.values.fails",
                    "extracted_jsonpath": "$.extracted.http_req_failed.fails",
                    "reason": (
                        "Schema requires using scenario-tagged $.metrics.http_req_failed{test_name:<scenario>}.values "
                        "when present, but source_jsonpath points to the untagged sibling metric."
                    ),
                }
            ]
        }
    )

    assert mismatches == []


def test_parse_mismatches_ignores_success_note_entries() -> None:
    """Verifier success notes inside mismatches are ignored."""
    mismatches = parse_mismatches(
        {
            "mismatches": [
                {
                    "field": "http_req_failed.fails",
                    "expected": 3342,
                    "actual": 3342,
                    "source_jsonpath": '$.source.metrics["http_req_failed{test_name:getSymbolsTree}"].values.fails',
                    "extracted_jsonpath": "$.extracted.http_req_failed.fails",
                    "reason": "Extracted value matches the schema-authorized tagged metric; no mismatch.",
                },
                {
                    "field": "http_req_failed.passes",
                    "expected": 5659,
                    "actual": 5659,
                    "source_jsonpath": '$.source.metrics["http_req_failed{test_name:getSymbolsTree}"].values.passes',
                    "extracted_jsonpath": "$.extracted.http_req_failed.passes",
                    "reason": "Extracted value matches the schema-authorized tagged metric; no mismatch.",
                },
                {
                    "field": "http_req_failed.rate",
                    "expected": 0.6287079213420731,
                    "actual": 0.6287079213420731,
                    "source_jsonpath": '$.source.metrics["http_req_failed{test_name:getSymbolsTree}"].values.rate',
                    "extracted_jsonpath": "$.extracted.http_req_failed.rate",
                    "reason": "Extracted value matches the schema-authorized tagged metric; no mismatch.",
                },
            ]
        }
    )

    assert mismatches == []


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
    source_payload: dict[str, Any] = {
        "testRunDurationMs": 60000,
        "env": None,
        "execScenarios": {
            "getVpsEligible": {
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
            "http_req_duration{test_name:getVpsEligible}": {
                "values": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                }
            },
            "http_req_blocked": {
                "values": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                }
            },
            "http_req_connecting": {
                "values": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                }
            },
            "http_req_receiving": {
                "values": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                }
            },
            "http_req_sending": {
                "values": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                }
            },
            "http_req_tls_handshaking": {
                "values": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                }
            },
            "http_req_waiting": {
                "values": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                }
            },
            "iteration_duration": {
                "values": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                }
            },
            "http_req_failed{test_name:getVpsEligible}": {"values": {"rate": 0.0, "passes": 100, "fails": 0}},
            "http_reqs": {"values": {"count": 100, "rate": 10.0}},
            "iterations": {"values": {"count": 100, "rate": 10.0}},
            "data_received": {"values": {"count": 1000, "rate": 100.0}},
            "data_sent": {"values": {"count": 500, "rate": 50.0}},
        },
        "thresholds": {"http_req_failed{test_name:getVpsEligible}": ["rate<0.01"]},
    }
    report_path.write_text(json.dumps(source_payload), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            {
                "service": "vps",
                "report_file": "report.json",
                "test_run_duration_ms": 60000,
                "scenario": {
                    "name": "getVpsEligible",
                    "env_name": "staging",
                    "executor": "constant-arrival-rate",
                    "rate": 10,
                    "duration": "1m",
                    "preAllocatedVUs": 10,
                    "maxVUs": 20,
                },
                "checks": {"rate": 1.0, "passes": 100, "fails": 0},
                "http_req_duration": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                },
                "http_req_blocked": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                },
                "http_req_connecting": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                },
                "http_req_receiving": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                },
                "http_req_sending": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                },
                "http_req_tls_handshaking": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                },
                "http_req_waiting": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                },
                "iteration_duration": {
                    "min": 1.0,
                    "avg": 2.0,
                    "med": 2.0,
                    "max": 3.0,
                    "p(95)": 2.5,
                    "p(99)": 2.9,
                },
                "http_req_failed": {"rate": 0.0, "passes": 100, "fails": 0},
                "http_reqs": {"count": 100, "rate": 10.0},
                "iterations": {"count": 100, "rate": 10.0},
                "data_received": {"count": 1000, "rate": 100.0},
                "data_sent": {"count": 500, "rate": 50.0},
                "dropped_iterations": None,
                "thresholds": {"http_req_failed{test_name:getVpsEligible}": ["rate<0.01"]},
            },
            {"mismatches": []},
        ]
    )
    parser = StubK6ParsedReportParser(
        K6ParsedReport(
            service="vps",
            scenarios=[
                K6Scenario(
                    source_report_file="report.json",
                    name="getVpsEligible",
                    env_name="staging",
                    executor="constant-arrival-rate",
                    rate=10.0,
                    duration="1m",
                    pre_allocated_vus=10,
                    max_vus=20,
                    test_run_duration_ms=60000.0,
                    thresholds={"http_req_failed{test_name:getVpsEligible}": ["rate<0.01"]},
                    metrics=source_payload["metrics"],
                    raw_payload=source_payload,
                )
            ],
        )
    )
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    service.extract(
        service="vps",
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


def test_verification_prompt_includes_report_file_context(tmp_path: Path) -> None:
    """Verification payload includes external report-file context."""
    report_path = tmp_path / "megatron-1.json"
    report_path.write_text(json.dumps(_source_payload()), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            {**_extracted_payload(), "report_file": "megatron-1.json"},
            {"mismatches": []},
        ]
    )
    parser = StubK6ParsedReportParser(_parsed_report(source_report_file="megatron-1.json"))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    service.extract(
        service="megatron",
        report_paths=[report_path],
    )

    verification_prompt_payload = json.loads(llm.calls[1][1])
    assert verification_prompt_payload["verification_context"]["report_file"] == "megatron-1.json"
    assert verification_prompt_payload["extracted"]["report_file"] == "megatron-1.json"
    assert verification_prompt_payload["target_schema"]["properties"]["report_file"]["description"] == (
        "Use verification_context.report_file, populated from the selected scenario source report filename"
    )


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
    assert len(result.runs) == 1
    assert result.overall_summary.status == "unknown"
    assert result.scenario_summaries[0].threshold_results[0].metric_key == "http_req_duration"
    assert "report_file" not in result.runs[0].extracted
    assert result.runs[0].extracted["scenario"]["name"] == "megatron-load"
    assert llm.calls == []


def test_extract_ignores_false_positive_match_reports_from_verifier(tmp_path: Path) -> None:
    """Extraction ignores verifier entries that confirm matching values."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_source_payload()), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            _extracted_payload(),
            {
                "mismatches": [
                    {
                        "field": "http_req_duration.avg",
                        "expected": 200.0,
                        "actual": 200.0,
                        "source_jsonpath": "$.source.metrics.http_req_duration.values.avg",
                        "extracted_jsonpath": "$.extracted.http_req_duration.avg",
                        "reason": "Extraction should use scenario-tagged metric when present; value matches.",
                    }
                ]
            },
        ]
    )
    parser = StubK6ParsedReportParser(_parsed_report())
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(
        service="megatron",
        report_paths=[report_path],
    )

    assert result.service == "megatron"
    assert len(result.runs) == 1


def test_extract_overrides_http_req_failed_with_exact_scenario_tagged_metric(tmp_path: Path) -> None:
    """Extraction uses exact scenario-tagged http_req_failed values when present."""
    report_path = tmp_path / "report.json"
    source_payload = _source_payload()
    source_payload["execScenarios"] = {
        "thdGetOrders": {
            "env_name": None,
            "tags": {"env_name": "staging"},
            "executor": "constant-arrival-rate",
            "rate": 10,
            "duration": "1m",
            "preAllocatedVUs": 10,
            "maxVUs": 20,
        }
    }
    source_payload["metrics"]["http_req_duration"] = {
        "values": {
            "min": 44.675271,
            "avg": 100.49421802188276,
            "med": 80.37146150000001,
            "max": 10075.100155,
            "p(95)": 177.24301234999987,
            "p(99)": 242.1808502500002,
        }
    }
    source_payload["metrics"]["http_req_duration{test_name:thdGetOrders}"] = {
        "values": {
            "min": 44.675271,
            "avg": 100.06499275127425,
            "med": 80.3342385,
            "max": 10075.100155,
            "p(95)": 176.82212119999994,
            "p(99)": 238.19634724000014,
        }
    }
    source_payload["metrics"]["http_req_failed"] = {"values": {"rate": 0.000133248730964467, "passes": 21, "fails": 157579}}
    source_payload["metrics"]["http_req_failed{test_name:thdGetOrders}"] = {"values": {"rate": 0.00013333333333333334, "passes": 21, "fails": 157479}}
    report_path.write_text(json.dumps(source_payload), encoding="utf-8")

    extracted_payload = _extracted_payload()
    extracted_payload["service"] = "tradinghistoricaldata"
    extracted_payload["scenario"]["name"] = "thdGetOrders"
    extracted_payload["http_req_duration"] = source_payload["metrics"]["http_req_duration"]["values"]
    extracted_payload["http_req_failed"] = source_payload["metrics"]["http_req_failed"]["values"]

    llm = StubStructuredLlm([extracted_payload, {"mismatches": []}])
    parser = StubK6ParsedReportParser(
        _parsed_report_with_source_payload(
            source_payload=source_payload,
            service="tradinghistoricaldata",
        )
    )
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(service="tradinghistoricaldata", report_paths=[report_path])

    assert result.runs[0].extracted["http_req_failed"] == {
        "rate": 0.00013333333333333334,
        "passes": 21,
        "fails": 157479,
    }
    assert result.runs[0].extracted["http_req_duration"] == {
        "min": 44.675271,
        "avg": 100.06499275127425,
        "med": 80.3342385,
        "max": 10075.100155,
        "p(95)": 176.82212119999994,
        "p(99)": 238.19634724000014,
    }


def test_extract_keeps_generic_http_req_failed_when_exact_scenario_tagged_metric_is_absent(tmp_path: Path) -> None:
    """Extraction falls back to generic http_req_failed when no exact tag exists."""
    report_path = tmp_path / "report.json"
    source_payload = _source_payload()
    source_payload["metrics"]["http_req_failed"] = {"values": {"rate": 0.25, "passes": 75, "fails": 25}}
    source_payload["metrics"]["http_req_failed{expected_response:true}"] = {"values": {"rate": 0.5, "passes": 50, "fails": 50}}
    report_path.write_text(json.dumps(source_payload), encoding="utf-8")

    extracted_payload = _extracted_payload()
    extracted_payload["http_req_failed"] = {"rate": 0.5, "passes": 50, "fails": 50}

    llm = StubStructuredLlm([extracted_payload, {"mismatches": []}])
    parser = StubK6ParsedReportParser(_parsed_report_with_source_payload(source_payload=source_payload))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(service="megatron", report_paths=[report_path])

    assert result.runs[0].extracted["http_req_failed"] == {
        "rate": 0.25,
        "passes": 75,
        "fails": 25,
    }


def test_extract_overrides_dropped_iterations_when_source_metric_is_present(tmp_path: Path) -> None:
    """Extraction uses source dropped_iterations values even when model returns null."""
    report_path = tmp_path / "report.json"
    source_payload = _source_payload()
    report_path.write_text(json.dumps(source_payload), encoding="utf-8")

    extracted_payload = _extracted_payload()
    extracted_payload["dropped_iterations"] = None

    llm = StubStructuredLlm([extracted_payload, {"mismatches": []}])
    parser = StubK6ParsedReportParser(_parsed_report_with_source_payload(source_payload=source_payload))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(service="megatron", report_paths=[report_path])

    assert result.runs[0].extracted["dropped_iterations"] == {"count": 0, "rate": 0.0}


def test_extract_keeps_null_dropped_iterations_when_source_metric_is_absent(tmp_path: Path) -> None:
    """Extraction keeps null dropped_iterations when source metric is absent."""
    report_path = tmp_path / "report.json"
    source_payload = _source_payload()
    source_payload["metrics"].pop("dropped_iterations", None)
    report_path.write_text(json.dumps(source_payload), encoding="utf-8")

    extracted_payload = _extracted_payload()
    extracted_payload["dropped_iterations"] = None

    llm = StubStructuredLlm([extracted_payload, {"mismatches": []}])
    parser = StubK6ParsedReportParser(_parsed_report_with_source_payload(source_payload=source_payload))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(service="megatron", report_paths=[report_path])

    assert result.runs[0].extracted["dropped_iterations"] is None


def test_extract_populates_missing_dropped_iterations_from_source_metric(tmp_path: Path) -> None:
    """Extraction restores dropped_iterations when the model omits the field."""
    report_path = tmp_path / "report.json"
    source_payload = _source_payload()
    report_path.write_text(json.dumps(source_payload), encoding="utf-8")

    extracted_payload = _extracted_payload()
    extracted_payload.pop("dropped_iterations", None)

    llm = StubStructuredLlm([extracted_payload, {"mismatches": []}])
    parser = StubK6ParsedReportParser(_parsed_report_with_source_payload(source_payload=source_payload))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(service="megatron", report_paths=[report_path])

    assert result.runs[0].extracted["dropped_iterations"] == {"count": 0, "rate": 0.0}


def test_verification_prompt_prefers_exact_test_name_tag_over_other_tagged_variants(tmp_path: Path) -> None:
    """Verification guidance ignores unrelated tagged metrics when scenario tag is absent."""
    report_path = tmp_path / "report.json"
    source_payload = _source_payload()
    source_payload["metrics"]["http_req_duration"] = {
        "values": {
            "min": 80.0,
            "avg": 82.82120936664543,
            "med": 67.061436,
            "max": 300.0,
            "p(95)": 172.0713248,
            "p(99)": 261.9299220200001,
        }
    }
    source_payload["metrics"]["http_req_duration{expected_response:true}"] = {
        "values": {
            "min": 80.0,
            "avg": 82.7747486743537,
            "med": 67.06140400000001,
            "max": 300.0,
            "p(95)": 172.06033974999988,
            "p(99)": 261.7865649299996,
        }
    }
    report_path.write_text(json.dumps(source_payload), encoding="utf-8")

    llm = StubStructuredLlm([_extracted_payload(), {"mismatches": []}])
    parser = StubK6ParsedReportParser(_parsed_report_with_source_payload(source_payload=source_payload))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    service.extract(service="megatron", report_paths=[report_path])

    verification_prompt_payload = json.loads(llm.calls[1][1])
    http_req_duration_schema = verification_prompt_payload["target_schema"]["properties"]["http_req_duration"]
    rules = verification_prompt_payload["rules"]

    assert "Ignore other tagged variants" in http_req_duration_schema["description"]
    assert any("unrelated tagged variants" in rule for rule in rules)
    assert any("no exact test_name:<scenario> tagged metric exists" in rule.lower() for rule in rules)


def test_parse_mismatches_ignores_unrelated_tagged_metric_false_positive() -> None:
    """Verifier mismatch is ignored when it prefers an unrelated non-scenario tag."""
    mismatches = parse_mismatches(
        {
            "mismatches": [
                {
                    "field": "http_req_duration.avg",
                    "expected": 82.7747486743537,
                    "actual": 82.82120936664543,
                    "extracted_jsonpath": "$.extracted.http_req_duration.avg",
                    "reason": (
                        "Schema requires scenario-tagged http_req_duration{test_name:<scenario>} when present; it is absent, "
                        "so untagged http_req_duration.values should be used. Extracted used untagged values, but source "
                        "contains an additional tagged variant; per schema guidance, the tagged metric should be preferred, "
                        "and the only tagged http_req_duration available is {expected_response:true}."
                    ),
                    "source_jsonpath": '$.source.metrics["http_req_duration{expected_response:true}"].values.avg',
                }
            ]
        }
    )

    assert mismatches == []


def test_parse_mismatches_ignores_verifier_mismatch_when_payload_values_match() -> None:
    """Verifier mismatch is ignored when source and extracted payload values actually match."""
    mismatches = parse_mismatches(
        {
            "mismatches": [
                {
                    "field": "http_req_failed.fails",
                    "expected": 157479,
                    "actual": 157579,
                    "source_jsonpath": '$.source.metrics["http_req_failed{test_name:thdGetOrders}"].values.fails',
                    "extracted_jsonpath": "$.extracted.http_req_failed.fails",
                    "reason": "Schema requires exact scenario-tagged http_req_failed{test_name:<scenario>} when present; extracted used untagged fails value instead.",
                }
            ]
        },
        source_payload={
            "metrics": {
                "http_req_failed{test_name:thdGetOrders}": {"values": {"fails": 157479}},
            }
        },
        extracted_payload={
            "http_req_failed": {"fails": 157479},
        },
    )

    assert mismatches == []


def test_parse_mismatches_keeps_real_mismatch_when_payload_values_differ() -> None:
    """Verifier mismatch is kept when source and extracted payload values differ."""
    mismatches = parse_mismatches(
        {
            "mismatches": [
                {
                    "field": "http_req_failed.fails",
                    "expected": 157479,
                    "actual": 157579,
                    "source_jsonpath": '$.source.metrics["http_req_failed{test_name:thdGetOrders}"].values.fails',
                    "extracted_jsonpath": "$.extracted.http_req_failed.fails",
                    "reason": "value mismatch",
                }
            ]
        },
        source_payload={
            "metrics": {
                "http_req_failed{test_name:thdGetOrders}": {"values": {"fails": 157479}},
            }
        },
        extracted_payload={
            "http_req_failed": {"fails": 157579},
        },
    )

    assert len(mismatches) == 1
    assert mismatches[0].field == "http_req_failed.fails"


def test_extract_builds_symbolstreeservice_post_processed_group(tmp_path: Path) -> None:
    """Extraction returns grouped derived runs for numbered symbol tree scenarios."""
    report_path_1 = tmp_path / "symbolstreeservice-1.json"
    report_path_2 = tmp_path / "symbolstreeservice-2.json"
    report_path_3 = tmp_path / "symbolstreeservice-3.json"
    report_path_1.write_text(json.dumps(_source_payload()), encoding="utf-8")
    report_path_2.write_text(json.dumps(_source_payload()), encoding="utf-8")
    report_path_3.write_text(json.dumps(_source_payload()), encoding="utf-8")

    llm = StubStructuredLlm(
        [
            _symbolstreeservice_extracted_payload(
                scenario_name="getSymbolsTreeInfo1",
                report_file="symbolstreeservice-1.json",
            ),
            {"mismatches": []},
            _symbolstreeservice_extracted_payload(
                scenario_name="getSymbolsTreeInfo7",
                report_file="symbolstreeservice-2.json",
            ),
            {"mismatches": []},
            _symbolstreeservice_passthrough_payload(report_file="symbolstreeservice-3.json"),
            {"mismatches": []},
        ]
    )
    parser = StubK6ParsedReportParser(_parsed_report(service="symbolstreeservice"))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(
        service="symbolstreeservice",
        report_paths=[report_path_1, report_path_2, report_path_3],
    )

    assert len(result.runs) == 2
    assert [run.extracted["scenario"]["name"] for run in result.runs] == ["getSymbolsTree", "getSymbolsTreeInfo"]
    passthrough_run = result.runs[0]
    assert passthrough_run.source_report_files == ["symbolstreeservice-3.json"]
    assert "report_file" not in passthrough_run.extracted
    assert passthrough_run.extracted["scenario"]["name"] == "getSymbolsTree"

    grouped_run = result.runs[1]
    assert grouped_run.source_report_files == ["symbolstreeservice-1.json", "symbolstreeservice-2.json"]
    assert "report_file" not in grouped_run.extracted
    assert grouped_run.extracted["scenario"]["name"] == "getSymbolsTreeInfo"
    assert grouped_run.extracted["group_size"] == 2
    assert grouped_run.extracted["source_scenarios"] == ["getSymbolsTreeInfo1", "getSymbolsTreeInfo7"]
    assert grouped_run.extracted["scenario"]["rate"] == 20
    assert grouped_run.extracted["scenario"]["preAllocatedVUs"] == 10
    assert grouped_run.extracted["scenario"]["maxVUs"] == 20
    assert grouped_run.extracted["test_run_duration_ms"] == 60000
    assert grouped_run.extracted["iterations"] == {"count": 200, "rate": 20.0}
    assert grouped_run.extracted["http_reqs"] == {"count": 200, "rate": 20.0}
    assert grouped_run.extracted["data_received"] == {"count": 2000, "rate": 200.0}
    assert grouped_run.extracted["data_sent"] == {"count": 1000, "rate": 100.0}
    assert grouped_run.extracted["dropped_iterations"] == {"count": 0, "rate": 0.0}
    assert grouped_run.extracted["checks"] == {"rate": 0.0, "passes": 200, "fails": 0}
    assert grouped_run.extracted["http_req_failed"] == {"rate": 0.0, "passes": 200, "fails": 0}
    assert grouped_run.extracted["http_req_duration"] == {
        "min": 100.0,
        "avg": 200.0,
        "med": 150.0,
        "max": 900.0,
        "p(95)": 400.0,
        "p(99)": 700.0,
    }
    assert grouped_run.extracted["thresholds"] == {"http_req_duration{test_name:getSymbolsTreeInfo}": ["p(95)<1000"]}
    assert grouped_run.extracted["threshold_results"] == []


def test_extract_uses_max_duration_when_grouped_runs_differ(tmp_path: Path) -> None:
    """Grouped duration uses max when source run durations differ."""
    report_path_1 = tmp_path / "symbolstreeservice-1.json"
    report_path_2 = tmp_path / "symbolstreeservice-2.json"
    report_path_1.write_text(json.dumps(_source_payload()), encoding="utf-8")
    report_path_2.write_text(json.dumps(_source_payload()), encoding="utf-8")

    first_payload = _symbolstreeservice_extracted_payload(
        scenario_name="getSymbolsTreeInfo1",
        report_file="symbolstreeservice-1.json",
    )
    second_payload = _symbolstreeservice_extracted_payload(
        scenario_name="getSymbolsTreeInfo7",
        report_file="symbolstreeservice-2.json",
    )
    second_payload["test_run_duration_ms"] = 62000

    llm = StubStructuredLlm(
        [
            first_payload,
            {"mismatches": []},
            second_payload,
            {"mismatches": []},
        ]
    )
    parser = StubK6ParsedReportParser(_parsed_report(service="symbolstreeservice"))
    service = K6ServiceExtractionService(llm=llm, parser=parser)

    result = service.extract(
        service="symbolstreeservice",
        report_paths=[report_path_1, report_path_2],
    )

    assert len(result.runs) == 1
    assert result.runs[0].extracted["test_run_duration_ms"] == 62000


def test_extract_writes_model_snapshots_for_service_specific_flow(tmp_path: Path) -> None:
    """Extraction writes extraction, post-processed, and summary snapshots."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_source_payload()), encoding="utf-8")
    llm = StubStructuredLlm([_extracted_payload(), {"mismatches": []}])
    parser = StubK6ParsedReportParser(_parsed_report())
    debug_writer = SpyDebugJsonWriter()
    service = K6ServiceExtractionService(
        llm=llm,
        parser=parser,
        debug_config=K6ServiceExtractionDebugConfig(
            model_debug_json_writer=debug_writer,
            model_debug_json_enabled=True,
        ),
    )

    result = service.extract(service="megatron", report_paths=[report_path])

    assert result.service == "megatron"
    assert [label for label, _ in debug_writer.calls] == [
        "extraction_runs",
        "post_processed_runs",
        "summary_output",
    ]


def test_extract_writes_model_snapshots_for_generic_flow(tmp_path: Path) -> None:
    """Generic extraction writes consistent model snapshots."""
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_source_payload()), encoding="utf-8")
    llm = StubStructuredLlm([])
    parser = StubK6ParsedReportParser(_parsed_report(service="unknown-service"))
    debug_writer = SpyDebugJsonWriter()
    service = K6ServiceExtractionService(
        llm=llm,
        parser=parser,
        debug_config=K6ServiceExtractionDebugConfig(
            model_debug_json_writer=debug_writer,
            model_debug_json_enabled=True,
        ),
    )

    result = service.extract(service="unknown-service", report_paths=[report_path])

    assert result.mode == "generic"
    assert [label for label, _ in debug_writer.calls] == [
        "extraction_runs",
        "post_processed_runs",
        "summary_output",
    ]


def test_parse_mismatches_preserves_numeric_values() -> None:
    """Mismatch parsing preserves JSON-scalar numeric values."""
    mismatches = parse_mismatches(
        {
            "mismatches": [
                {
                    "field": "http_reqs.count",
                    "expected": 100,
                    "actual": 101,
                    "source_jsonpath": "$.metrics.http_reqs.values.count",
                    "extracted_jsonpath": "$.http_reqs.count",
                    "reason": "value mismatch",
                }
            ]
        }
    )

    assert len(mismatches) == 1
    assert mismatches[0].expected == 100
    assert mismatches[0].actual == 101
