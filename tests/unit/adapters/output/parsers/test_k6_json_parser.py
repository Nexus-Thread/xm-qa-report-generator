"""Unit tests for the k6 JSON summary report parser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from qa_report_generator.adapters.output.parsers import K6JsonParser
from qa_report_generator.domain.exceptions import (
    ParseFileNotFoundError,
    ParseInvalidFormatError,
    ParseInvalidJsonError,
)
from qa_report_generator.domain.value_objects import Duration, TestStatus

if TYPE_CHECKING:
    from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_summary_payload() -> dict:
    """Minimal valid k6 summary export with checks and thresholds."""
    return {
        "metrics": {
            "http_req_duration": {
                "type": "trend",
                "contains": "time",
                "values": {"avg": 155.0, "min": 100.0, "max": 300.0, "p(95)": 250.0, "count": 1000, "rate": 33.3},
                "thresholds": {
                    "p(95)<500": {"ok": True},
                    "avg<200": {"ok": False},
                },
            },
            "checks": {
                "type": "rate",
                "values": {"passes": 980, "fails": 20, "rate": 0.98},
            },
            "iterations": {
                "type": "counter",
                "values": {"count": 1000, "rate": 33.3},
            },
        },
        "root_group": {
            "name": "",
            "path": "",
            "id": "root",
            "checks": [
                {"name": "status is 200", "path": "::status is 200", "id": "c1", "passes": 990, "fails": 10},
                {"name": "response < 500ms", "path": "::response < 500ms", "id": "c2", "passes": 1000, "fails": 0},
            ],
            "groups": [
                {
                    "name": "auth",
                    "path": "::auth",
                    "id": "g1",
                    "checks": [
                        {"name": "token valid", "path": "::auth::token valid", "id": "c3", "passes": 500, "fails": 0},
                    ],
                    "groups": [],
                }
            ],
        },
        "state": {
            "testRunDurationMs": 30000,
        },
    }


def test_parse_happy_path_counts(tmp_path: Path) -> None:
    """Parser should map checks and thresholds to correct total/passed/failed counts."""
    path = tmp_path / "summary.json"
    _write_json(path, _make_summary_payload())

    metrics = K6JsonParser().parse(path)

    # 3 checks + 2 thresholds = 5 total
    assert metrics.total == 5
    # passing: 1 root check (response<500ms) + 1 auth check (token valid) + 1 threshold (p(95)<500) = 3
    assert metrics.passed == 3
    # failing: 1 root check (status is 200, fails=10) + 1 threshold (avg<200) = 2
    assert metrics.failed == 2
    # validator satisfied
    assert metrics.total == metrics.passed + metrics.failed + metrics.skipped + metrics.errors


def test_parse_duration_from_state(tmp_path: Path) -> None:
    """Parser should extract duration from state.testRunDurationMs."""
    path = tmp_path / "summary.json"
    _write_json(path, _make_summary_payload())

    metrics = K6JsonParser().parse(path)

    assert metrics.duration == Duration(seconds=30.0)


def test_parse_failures_include_failed_check(tmp_path: Path) -> None:
    """Parser should produce a Failure for each check with fails > 0."""
    path = tmp_path / "summary.json"
    _write_json(path, _make_summary_payload())

    metrics = K6JsonParser().parse(path)

    check_failures = [f for f in metrics.failures if f.type == "CheckFailure"]
    assert len(check_failures) == 1
    failure = check_failures[0]
    assert failure.test_name == "status is 200"
    assert "10/1000" in failure.message


def test_parse_failures_include_threshold_violation(tmp_path: Path) -> None:
    """Parser should produce a Failure for each violated threshold."""
    path = tmp_path / "summary.json"
    _write_json(path, _make_summary_payload())

    metrics = K6JsonParser().parse(path)

    threshold_failures = [f for f in metrics.failures if f.type == "ThresholdViolation"]
    assert len(threshold_failures) == 1
    failure = threshold_failures[0]
    assert failure.test_name == "avg<200"
    assert "http_req_duration" in failure.message


def test_parse_test_results_include_all_checks_and_thresholds(tmp_path: Path) -> None:
    """Parser should create one TestCaseResult per check and per threshold."""
    path = tmp_path / "summary.json"
    _write_json(path, _make_summary_payload())

    metrics = K6JsonParser().parse(path)

    assert len(metrics.test_results) == 5  # 3 checks + 2 thresholds
    statuses = {r.test_name: r.status for r in metrics.test_results}
    assert statuses["status is 200"] == TestStatus.FAILED
    assert statuses["response < 500ms"] == TestStatus.PASSED
    assert statuses["token valid"] == TestStatus.PASSED
    assert statuses["p(95)<500"] == TestStatus.PASSED
    assert statuses["avg<200"] == TestStatus.FAILED


def test_parse_nested_group_suite_name(tmp_path: Path) -> None:
    """Checks in nested groups should use hierarchical suite names."""
    path = tmp_path / "summary.json"
    _write_json(path, _make_summary_payload())

    metrics = K6JsonParser().parse(path)

    suites = {r.test_name: r.suite for r in metrics.test_results}
    assert suites["token valid"] == "auth"
    assert suites["status is 200"] == "root"


def test_parse_no_checks_no_thresholds(tmp_path: Path) -> None:
    """A k6 report with zero checks and zero thresholds should produce RunMetrics with total=0."""
    payload = {
        "metrics": {},
        "root_group": {"name": "", "path": "", "id": "root", "checks": [], "groups": []},
    }
    path = tmp_path / "summary.json"
    _write_json(path, payload)

    metrics = K6JsonParser().parse(path)

    assert metrics.total == 0
    assert metrics.passed == 0
    assert metrics.failed == 0
    assert metrics.failures == []
    assert metrics.test_results == []
    assert metrics.duration is None


def test_parse_duration_fallback_to_iter_duration(tmp_path: Path) -> None:
    """Parser should fall back to iteration_duration avg * count when state is absent."""
    payload = {
        "metrics": {
            "iteration_duration": {"type": "trend", "values": {"avg": 1000.0}},
            "iterations": {"type": "counter", "values": {"count": 50}},
        },
        "root_group": {"name": "", "path": "", "id": "root", "checks": [], "groups": []},
    }
    path = tmp_path / "summary.json"
    _write_json(path, payload)

    metrics = K6JsonParser().parse(path)

    # 1000ms * 50 / 1000 = 50s
    assert metrics.duration == Duration(seconds=50.0)


def test_parse_missing_file_raises_error(tmp_path: Path) -> None:
    """Missing file should raise ParseFileNotFoundError."""
    with pytest.raises(ParseFileNotFoundError):
        K6JsonParser().parse(tmp_path / "missing.json")


def test_parse_invalid_json_raises_error(tmp_path: Path) -> None:
    """Malformed JSON should raise ParseInvalidJsonError."""
    path = tmp_path / "bad.json"
    path.write_text("{bad json", encoding="utf-8")
    with pytest.raises(ParseInvalidJsonError):
        K6JsonParser().parse(path)


def test_parse_invalid_structure_raises_error(tmp_path: Path) -> None:
    """Wrong structure should raise ParseInvalidFormatError."""
    path = tmp_path / "bad.json"
    # root_group.checks must be a list; a string will cause extraction to fail
    _write_json(path, {"metrics": {}, "root_group": {"checks": "not-a-list", "groups": []}})
    with pytest.raises(ParseInvalidFormatError):
        K6JsonParser().parse(path)
