"""Unit tests for the pytest JSON report parser."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from qa_report_generator.adapters.output.parsers import PytestJsonParser
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


def _make_report_payload() -> dict:
    return {
        "summary": {
            "total": 3,
            "passed": 1,
            "failed": 1,
            "skipped": 1,
            "error": 0,
        },
        "duration": 12.5,
        "tests": [
            {
                "nodeid": "tests/test_alpha.py::test_pass",
                "outcome": "passed",
                "duration": 0.2,
            },
            {
                "nodeid": "tests/test_beta.py::TestThing::test_fail",
                "outcome": "failed",
                "duration": 0.8,
                "setup": {"stdout": "setup out", "stderr": None, "log": None},
                "call": {
                    "longrepr": {
                        "reprcrash": {
                            "message": "AssertionError: boom",
                            "path": "AssertionError",
                        },
                    },
                    "stdout": "call out",
                    "stderr": "call err",
                    "log": "call log",
                },
                "teardown": {"stdout": None, "stderr": None, "log": None},
            },
            {
                "nodeid": "tests/test_gamma.py::test_skip",
                "outcome": "skipped",
                "duration": 0.1,
            },
        ],
    }


def test_parse_happy_path_includes_failures_and_outputs(tmp_path: Path) -> None:
    """Parser should extract metrics, failures, and captured output."""
    report_path = tmp_path / "report.json"
    _write_json(report_path, _make_report_payload())

    metrics = PytestJsonParser().parse(report_path)

    assert metrics.total == 3
    assert metrics.failed == 1
    assert metrics.duration == Duration(seconds=12.5)
    assert len(metrics.failures) == 1
    failure = metrics.failures[0]
    assert failure.test_name == "test_fail"
    assert failure.suite == "tests.test_beta.TestThing"
    assert failure.message == "AssertionError: boom"
    assert failure.output
    assert failure.output.stdout is not None
    assert "[setup]" in failure.output.stdout
    assert "setup out" in failure.output.stdout
    assert "[call]" in failure.output.stdout
    assert "call out" in failure.output.stdout
    assert failure.output.stderr is not None
    assert "call err" in failure.output.stderr
    assert failure.output.log is not None
    assert "call log" in failure.output.log


def test_parse_collects_test_results(tmp_path: Path) -> None:
    """Parser should store test case results for analytics."""
    report_path = tmp_path / "report.json"
    _write_json(report_path, _make_report_payload())

    metrics = PytestJsonParser().parse(report_path)

    assert len(metrics.test_results) == 3
    statuses = {result.test_name: result.status for result in metrics.test_results}
    assert statuses["test_pass"] == TestStatus.PASSED
    assert statuses["test_fail"] == TestStatus.FAILED
    assert statuses["test_skip"] == TestStatus.SKIPPED


def test_parse_missing_file_raises_domain_error(tmp_path: Path) -> None:
    """Missing report file should raise ParseFileNotFoundError."""
    report_path = tmp_path / "missing.json"

    with pytest.raises(ParseFileNotFoundError):
        PytestJsonParser().parse(report_path)


def test_parse_invalid_json_raises_domain_error(tmp_path: Path) -> None:
    """Invalid JSON should raise ParseInvalidJsonError with context."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ParseInvalidJsonError):
        PytestJsonParser().parse(report_path)


def test_parse_invalid_format_raises_domain_error(tmp_path: Path) -> None:
    """Malformed structure should raise ParseInvalidFormatError."""
    report_path = tmp_path / "report.json"
    _write_json(report_path, {"summary": "not-a-dict", "tests": "bad"})

    with pytest.raises(ParseInvalidFormatError):
        PytestJsonParser().parse(report_path)


def test_parse_unknown_outcome_defaults_to_error(tmp_path: Path) -> None:
    """Unknown outcome should default to TestStatus.ERROR in results."""
    report_path = tmp_path / "report.json"
    payload = _make_report_payload()
    payload["tests"].append(
        {
            "nodeid": "tests/test_delta.py::test_unknown",
            "outcome": "flaky",
            "duration": 0.05,
        },
    )
    payload["summary"]["total"] = 4
    payload["summary"]["passed"] = 1
    payload["summary"]["failed"] = 1
    payload["summary"]["skipped"] = 1
    payload["summary"]["error"] = 1
    _write_json(report_path, payload)

    metrics = PytestJsonParser().parse(report_path)

    statuses = {result.test_name: result.status for result in metrics.test_results}
    assert statuses["test_unknown"] == TestStatus.ERROR


def test_parse_error_outcome_creates_failure(tmp_path: Path) -> None:
    """Error outcome should be treated as a failure."""
    report_path = tmp_path / "report.json"
    payload = {
        "summary": {
            "total": 1,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 1,
        },
        "tests": [
            {
                "nodeid": "tests/test_error.py::test_error",
                "outcome": "error",
                "duration": 0.5,
                "call": {
                    "crash": {
                        "message": "RuntimeError: boom",
                        "path": "RuntimeError",
                    },
                },
            },
        ],
    }
    _write_json(report_path, payload)

    metrics = PytestJsonParser().parse(report_path)

    assert len(metrics.failures) == 1
    failure = metrics.failures[0]
    assert failure.message == "RuntimeError: boom"
    assert failure.type == "RuntimeError"
