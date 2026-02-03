"""Unit tests for report diffing."""

from __future__ import annotations

from qa_report_generator.domain.analytics.report_diff import diff_runs
from qa_report_generator.domain.models import RunMetrics, TestCaseResult
from qa_report_generator.domain.value_objects import Duration, TestIdentifier, TestStatus


def _make_metrics(results: list[TestCaseResult]) -> RunMetrics:
    total = len(results)
    passed = sum(1 for result in results if result.status is TestStatus.PASSED)
    failed = sum(1 for result in results if result.status is TestStatus.FAILED)
    errors = sum(1 for result in results if result.status is TestStatus.ERROR)
    skipped = total - passed - failed - errors
    return RunMetrics(
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        errors=errors,
        duration=Duration(seconds=1.0),
        failures=[],
        test_results=results,
    )


def test_diff_runs_detects_regressions_and_fixes() -> None:
    """Diff should categorize new failures, fixes, and regressions."""
    previous = _make_metrics(
        [
            TestCaseResult(
                identifier=TestIdentifier(name="test_ok", suite="suite"),
                status=TestStatus.PASSED,
                duration=None,
            ),
            TestCaseResult(
                identifier=TestIdentifier(name="test_fail", suite="suite"),
                status=TestStatus.FAILED,
                duration=None,
            ),
        ]
    )
    current = _make_metrics(
        [
            TestCaseResult(
                identifier=TestIdentifier(name="test_ok", suite="suite"),
                status=TestStatus.FAILED,
                duration=None,
            ),
            TestCaseResult(
                identifier=TestIdentifier(name="test_new", suite="suite"),
                status=TestStatus.ERROR,
                duration=None,
            ),
        ]
    )

    diff = diff_runs(previous, current)

    assert {item.name for item in diff.regressions} == {"test_ok"}
    assert {item.name for item in diff.new_failures} == {"test_new"}
    assert {item.name for item in diff.fixed_tests} == {"test_fail"}
