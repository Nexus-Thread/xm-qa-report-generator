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

    parsed_report = parser.parse(service="megatron", report_files=[report_path])

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


def test_parse_raises_configuration_error_on_invalid_json(tmp_path: Path) -> None:
    """Parser raises a configuration error for invalid JSON reports."""
    report_path = tmp_path / "broken.json"
    report_path.write_text("{", encoding="utf-8")

    parser = K6ParsedReportParser()

    with pytest.raises(ConfigurationError):
        parser.parse(service="megatron", report_files=[report_path])


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
