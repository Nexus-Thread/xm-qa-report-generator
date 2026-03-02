"""Unit tests for k6 summary table parser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from qa_report_generator.adapters.output.parsers import K6SummaryTableParser
from qa_report_generator.domain.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pathlib import Path


def test_parse_prefers_scenario_metric_values(tmp_path: Path) -> None:
    """Parser prefers scenario-tagged duration metric over generic metric."""
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps(
            {
                "execScenarios": {
                    "orders-load": {
                        "executor": "constant-arrival-rate",
                    }
                },
                "metrics": {
                    "http_req_duration": {
                        "values": {
                            "p(95)": 999.0,
                            "p(99)": 999.0,
                        }
                    },
                    "http_req_duration{test_name:orders-load}": {
                        "values": {
                            "p(95)": 150.0,
                            "p(99)": 200.0,
                        }
                    },
                    "checks": {
                        "values": {
                            "rate": 1.0,
                        }
                    },
                    "iterations": {
                        "values": {
                            "count": 42,
                            "rate": 4.2,
                        }
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    parser = K6SummaryTableParser()

    rows = parser.parse(report_files=[report_path])

    assert len(rows) == 1
    row = rows[0]
    assert row.scenario == "orders-load"
    assert row.p95_duration_ms == 150.0
    assert row.p99_duration_ms == 200.0
    assert row.iterations == 42
    assert row.request_rate == 4.2


def test_parse_raises_configuration_error_on_invalid_json(tmp_path: Path) -> None:
    """Parser raises a configuration error for invalid JSON reports."""
    report_path = tmp_path / "broken.json"
    report_path.write_text("{", encoding="utf-8")

    parser = K6SummaryTableParser()

    with pytest.raises(ConfigurationError):
        parser.parse(report_files=[report_path])
