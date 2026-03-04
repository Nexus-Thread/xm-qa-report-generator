"""Unit tests for parsed k6 report parser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from qa_report_generator.adapters.output.parsers import K6ParsedReportParser
from qa_report_generator.domain.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_builds_scenario_with_report_file_provenance(tmp_path: Path) -> None:
    """Parser builds scenario-centric report with source report file metadata."""
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "execScenarios": {
                    "orders-load": {
                        "tags": {"env_name": "staging"},
                        "executor": "constant-arrival-rate",
                        "rate": 42,
                        "duration": "1m",
                        "preAllocatedVUs": 10,
                        "maxVUs": 20,
                    }
                },
                "execThresholds": {
                    "http_req_duration{test_name:orders-load}": ["p(95)<300", "p(99)<600"],
                },
                "state": {"testRunDurationMs": 60000},
                "setup_data": {"large": "payload"},
                "root_group": {"ignored": True},
                "metrics": {
                    "checks": {
                        "type": "rate",
                        "contains": "default",
                        "values": {"rate": 1.0, "passes": 42, "fails": 0},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    parser = K6ParsedReportParser()

    parsed_report = parser.parse(
        service="megatron",
        report_files=[report_path],
        remove_keys=frozenset({"setup_data", "root_group"}),
    )

    assert parsed_report.service == "megatron"
    assert len(parsed_report.scenarios) == 1
    scenario = parsed_report.scenarios[0]
    assert scenario.source_report_file == "report.json"
    assert scenario.name == "orders-load"
    assert scenario.env_name == "staging"
    assert scenario.executor == "constant-arrival-rate"
    assert scenario.rate == 42.0
    assert scenario.duration == "1m"
    assert scenario.pre_allocated_vus == 10
    assert scenario.max_vus == 20
    assert scenario.test_run_duration_ms == 60000.0
    assert "checks" in scenario.metrics
    assert "http_req_duration{test_name:orders-load}" in scenario.thresholds
    assert "setup_data" not in scenario.raw_payload
    assert "root_group" not in scenario.raw_payload


def test_parse_keeps_top_level_keys_when_remove_keys_not_provided(tmp_path: Path) -> None:
    """Parser preserves full payload by default when no key filter is provided."""
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "execScenarios": {
                    "orders-load": {
                        "executor": "constant-arrival-rate",
                    }
                },
                "setup_data": {"large": "payload"},
                "root_group": {"ignored": True},
                "metrics": {},
            }
        ),
        encoding="utf-8",
    )

    parser = K6ParsedReportParser()
    parsed_report = parser.parse(service="megatron", report_files=[report_path])

    scenario = parsed_report.scenarios[0]
    assert "setup_data" in scenario.raw_payload
    assert "root_group" in scenario.raw_payload


def test_parse_raises_configuration_error_on_invalid_json(tmp_path: Path) -> None:
    """Parser raises a configuration error for invalid JSON reports."""
    report_path = tmp_path / "broken.json"
    report_path.write_text("{", encoding="utf-8")

    parser = K6ParsedReportParser()

    with pytest.raises(ConfigurationError):
        parser.parse(service="megatron", report_files=[report_path])


def test_parse_raises_configuration_error_on_missing_file(tmp_path: Path) -> None:
    """Parser raises a configuration error when report file cannot be read."""
    parser = K6ParsedReportParser()

    with pytest.raises(ConfigurationError, match="Unable to read k6 JSON report"):
        parser.parse(service="megatron", report_files=[tmp_path / "does-not-exist.json"])


def test_parse_raises_configuration_error_on_missing_exec_scenarios(tmp_path: Path) -> None:
    """Parser raises a configuration error when scenario definitions are absent."""
    report_path = tmp_path / "missing-scenarios.json"
    report_path.write_text(json.dumps({"metrics": {}}), encoding="utf-8")

    parser = K6ParsedReportParser()

    with pytest.raises(ConfigurationError, match="Missing execScenarios object"):
        parser.parse(service="megatron", report_files=[report_path])


def test_parse_raises_configuration_error_on_invalid_exec_scenario_shape(tmp_path: Path) -> None:
    """Parser raises a configuration error for malformed scenario fields."""
    report_path = tmp_path / "invalid-shape.json"
    report_path.write_text(
        json.dumps(
            {
                "execScenarios": {
                    "orders-load": {
                        "executor": "constant-arrival-rate",
                        "rate": -1,
                        "duration": "1m",
                        "preAllocatedVUs": 10,
                        "maxVUs": 20,
                    }
                },
                "metrics": {},
            }
        ),
        encoding="utf-8",
    )

    parser = K6ParsedReportParser()

    with pytest.raises(ConfigurationError, match="Invalid k6 report schema"):
        parser.parse(service="megatron", report_files=[report_path])


def test_parse_allows_missing_executor_specific_fields_with_defaults(tmp_path: Path) -> None:
    """Parser maps absent scenario fields to deterministic defaults."""
    report_path = tmp_path / "executor-specific-shape.json"
    report_path.write_text(
        json.dumps(
            {
                "execScenarios": {
                    "orders-load": {
                        "executor": "per-vu-iterations",
                    }
                },
                "metrics": {},
            }
        ),
        encoding="utf-8",
    )

    parser = K6ParsedReportParser()
    parsed_report = parser.parse(service="megatron", report_files=[report_path])
    scenario = parsed_report.scenarios[0]

    assert scenario.rate == 0.0
    assert scenario.duration == ""
    assert scenario.pre_allocated_vus == 0
    assert scenario.max_vus == 0


def test_parse_creates_independent_payload_structures_per_scenario(tmp_path: Path) -> None:
    """Parser provides independent mutable structures for each parsed scenario."""
    report_path = tmp_path / "two-scenarios.json"
    report_path.write_text(
        json.dumps(
            {
                "execScenarios": {
                    "orders-load": {
                        "executor": "constant-arrival-rate",
                        "rate": 10,
                        "duration": "1m",
                        "preAllocatedVUs": 1,
                        "maxVUs": 2,
                    },
                    "positions-load": {
                        "executor": "constant-arrival-rate",
                        "rate": 20,
                        "duration": "1m",
                        "preAllocatedVUs": 2,
                        "maxVUs": 4,
                    },
                },
                "execThresholds": {"http_req_duration": ["p(95)<300"]},
                "metrics": {"checks": {"values": {"rate": 1.0}}},
            }
        ),
        encoding="utf-8",
    )

    parser = K6ParsedReportParser()
    parsed_report = parser.parse(service="megatron", report_files=[report_path])
    first, second = parsed_report.scenarios

    first.thresholds["new"] = ["p(99)<500"]
    first.metrics["checks"]["contains"] = "first-only"
    first.raw_payload["extra"] = {"flag": True}

    assert "new" not in second.thresholds
    assert second.metrics["checks"].get("contains") is None
    assert "extra" not in second.raw_payload


def test_parse_drops_non_dict_metrics_payload_entries(tmp_path: Path) -> None:
    """Parser keeps only metric entries that are object-shaped."""
    report_path = tmp_path / "mixed-metrics.json"
    report_path.write_text(
        json.dumps(
            {
                "execScenarios": {
                    "orders-load": {
                        "executor": "constant-arrival-rate",
                        "rate": 10,
                        "duration": "1m",
                        "preAllocatedVUs": 1,
                        "maxVUs": 2,
                    }
                },
                "metrics": {
                    "checks": {"values": {"rate": 1.0}},
                    "invalid_metric": 10,
                },
            }
        ),
        encoding="utf-8",
    )

    parser = K6ParsedReportParser()
    parsed_report = parser.parse(service="megatron", report_files=[report_path])

    scenario = parsed_report.scenarios[0]
    assert "checks" in scenario.metrics
    assert "invalid_metric" not in scenario.metrics
