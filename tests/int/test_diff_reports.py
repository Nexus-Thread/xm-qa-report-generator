"""Integration tests for report diff workflow."""

from __future__ import annotations

import json

from qa_report_generator.adapters.output.parsers import PytestJsonParser
from qa_report_generator.application.use_cases import ReportComparisonService


def _write_pytest_report(
    path,  # noqa: ANN001 - pytest tmp_path provides Path at runtime
    *,
    summary: dict[str, int],
    tests: list[dict[str, object]],
) -> None:
    payload = {
        "summary": summary,
        "duration": 1.0,
        "tests": tests,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_diff_reports_end_to_end(tmp_path) -> None:  # noqa: ANN001
    """Parser → diff workflow should classify regressions, fixes, and new failures."""
    previous_path = tmp_path / "previous.json"
    current_path = tmp_path / "current.json"

    _write_pytest_report(
        previous_path,
        summary={"total": 2, "passed": 1, "failed": 1, "skipped": 0, "error": 0},
        tests=[
            {
                "nodeid": "tests/test_suite.py::test_ok",
                "outcome": "passed",
                "duration": 0.1,
            },
            {
                "nodeid": "tests/test_suite.py::test_fail",
                "outcome": "failed",
                "duration": 0.2,
            },
        ],
    )

    _write_pytest_report(
        current_path,
        summary={"total": 2, "passed": 0, "failed": 1, "skipped": 0, "error": 1},
        tests=[
            {
                "nodeid": "tests/test_suite.py::test_ok",
                "outcome": "failed",
                "duration": 0.15,
            },
            {
                "nodeid": "tests/test_suite.py::test_new",
                "outcome": "error",
                "duration": 0.25,
            },
        ],
    )

    parser = PytestJsonParser()
    service = ReportComparisonService(parser)
    diff = service.compare(previous_path, current_path)

    assert {item.name for item in diff.regressions} == {"test_ok"}
    assert {item.name for item in diff.new_failures} == {"test_new"}
    assert {item.name for item in diff.fixed_tests} == {"test_fail"}
