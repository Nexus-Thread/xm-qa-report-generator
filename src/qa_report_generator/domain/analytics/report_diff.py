"""Utilities for diffing test runs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.domain.analytics.models import ReportDiff
from qa_report_generator.domain.value_objects import TestIdentifier, TestStatus

if TYPE_CHECKING:
    from qa_report_generator.domain.models import RunMetrics


def diff_runs(previous: RunMetrics, current: RunMetrics) -> ReportDiff:
    """Compute the differences between two test runs."""
    previous_results = _build_status_map(previous)
    current_results = _build_status_map(current)

    new_failures: list[TestIdentifier] = []
    fixed_tests: list[TestIdentifier] = []
    regressions: list[TestIdentifier] = []

    for identifier, status in current_results.items():
        previous_status = previous_results.get(identifier)
        if _is_failure(status) and previous_status is None:
            new_failures.append(identifier)
        if previous_status and _is_pass(previous_status) and _is_failure(status):
            regressions.append(identifier)

    for identifier, status in previous_results.items():
        current_status = current_results.get(identifier)
        if _is_failure(status) and (current_status is None or _is_pass(current_status)):
            fixed_tests.append(identifier)

    return ReportDiff(
        new_failures=new_failures,
        fixed_tests=fixed_tests,
        regressions=regressions,
        total_previous=previous.total,
        total_current=current.total,
    )


def _build_status_map(metrics: RunMetrics) -> dict[TestIdentifier, TestStatus]:
    return {result.identifier: result.status for result in metrics.test_results}


def _is_failure(status: TestStatus) -> bool:
    return status in {TestStatus.FAILED, TestStatus.ERROR}


def _is_pass(status: TestStatus) -> bool:
    return status is TestStatus.PASSED
