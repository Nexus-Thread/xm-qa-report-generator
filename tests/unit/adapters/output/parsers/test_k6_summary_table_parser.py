"""Unit tests for consolidated k6 summary table parser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from qa_report_generator.adapters.output.parsers.performance import K6SummaryTableParser
from qa_report_generator.domain.exceptions import ParseFileNotFoundError, ParseInvalidFormatError, ParseInvalidJsonError

if TYPE_CHECKING:
    from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_payload() -> dict:
    return {
        "execScenarios": {
            "thdGetTradingHistory": {
                "rate": 40,
                "duration": "15m0s",
            }
        },
        "execThresholds": {
            "http_req_duration{test_name:thdGetTradingHistory}": ["p(99)<200", "p(95)<100"],
            "http_req_failed{test_name:thdGetTradingHistory}": ["rate<0.1"],
        },
        "metrics": {
            "iterations": {
                "values": {
                    "count": 36000,
                }
            },
            "http_req_duration{test_name:thdGetTradingHistory}": {
                "values": {
                    "med": 110.0,
                    "p(95)": 190.0,
                    "p(99)": 255.0,
                    "max": 1500.0,
                },
                "thresholds": {
                    "p(95)<100": {"ok": False},
                    "p(99)<200": {"ok": False},
                },
            },
            "http_req_failed{test_name:thdGetTradingHistory}": {
                "values": {
                    "rate": 0.03,
                },
                "thresholds": {
                    "rate<0.1": {"ok": True},
                },
            },
        },
    }


def test_parse_summary_row_happy_path(tmp_path: Path) -> None:
    """Parser should map k6 summary JSON to one normalized summary row."""
    report_path = tmp_path / "report.json"
    _write_json(report_path, _make_payload())

    row = K6SummaryTableParser().parse_summary_row(report_path)

    assert row.service == "THD"
    assert row.scenario == "thdGetTradingHistory"
    assert row.target_load_rps == 40
    assert row.duration_seconds == 900
    assert row.thresholds == ["p(95)<100", "p(99)<200", "rate<0.1"]
    assert row.iterations == 36000
    assert row.achieved_rps == 40.0
    assert row.latency_med_ms == 110.0
    assert row.latency_p95_ms == 190.0
    assert row.latency_p99_ms == 255.0
    assert row.latency_max_ms == 1500.0
    assert row.error_rate_percent == 3.0
    assert row.outcome_passed is False


def test_parse_summary_row_duration_fallback_to_state(tmp_path: Path) -> None:
    """Parser should fall back to state.testRunDurationMs when scenario duration is missing."""
    payload = _make_payload()
    payload["execScenarios"]["thdGetTradingHistory"].pop("duration")
    payload["state"] = {"testRunDurationMs": 120000}
    report_path = tmp_path / "report.json"
    _write_json(report_path, payload)

    row = K6SummaryTableParser().parse_summary_row(report_path)

    assert row.duration_seconds == 120
    assert row.achieved_rps == 300.0


def test_parse_summary_row_missing_file_raises(tmp_path: Path) -> None:
    """Parser should raise ParseFileNotFoundError for missing reports."""
    with pytest.raises(ParseFileNotFoundError):
        K6SummaryTableParser().parse_summary_row(tmp_path / "missing.json")


def test_parse_summary_row_invalid_json_raises(tmp_path: Path) -> None:
    """Parser should raise ParseInvalidJsonError for malformed JSON."""
    report_path = tmp_path / "broken.json"
    report_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ParseInvalidJsonError):
        K6SummaryTableParser().parse_summary_row(report_path)


def test_parse_summary_row_missing_scenario_raises(tmp_path: Path) -> None:
    """Parser should raise ParseInvalidFormatError when execScenarios is absent."""
    report_path = tmp_path / "report.json"
    _write_json(report_path, {"metrics": {}})

    with pytest.raises(ParseInvalidFormatError, match="execScenarios"):
        K6SummaryTableParser().parse_summary_row(report_path)
