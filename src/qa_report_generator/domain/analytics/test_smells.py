"""Detect test smells in a test run."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.domain.analytics.models import TestSmell

if TYPE_CHECKING:
    from qa_report_generator.domain.models import RunMetrics


class TestSmellDetector:
    """Detect common test smells from run metrics."""

    def detect(self, metrics: RunMetrics) -> list[TestSmell]:
        """Detect test smells based on durations, names, and output volume."""
        smells: list[TestSmell] = []

        long_tests = [result.test_name for result in metrics.test_results if result.duration is not None and result.duration.seconds > 30]
        if long_tests:
            smells.append(
                TestSmell(
                    smell_type="long_running",
                    description="Tests exceeding 30s runtime",
                    affected_tests=long_tests,
                    severity="medium",
                )
            )

        generic_names = [result.test_name for result in metrics.test_results if result.test_name.lower() in {"test", "test_all", "test_case", "test1"}]
        if generic_names:
            smells.append(
                TestSmell(
                    smell_type="generic_name",
                    description="Tests with generic names",
                    affected_tests=generic_names,
                    severity="low",
                )
            )

        high_output_tests = [
            failure.test_name for failure in metrics.failures if failure.output and (len(failure.output.stdout or "") + len(failure.output.stderr or "")) > 2000
        ]
        if high_output_tests:
            smells.append(
                TestSmell(
                    smell_type="excessive_output",
                    description="Failures with excessive stdout/stderr output",
                    affected_tests=high_output_tests,
                    severity="low",
                )
            )

        skipped_tests = [result.test_name for result in metrics.test_results if result.status.value == "skipped"]
        if skipped_tests:
            smells.append(
                TestSmell(
                    smell_type="skipped_tests",
                    description="Skipped tests detected",
                    affected_tests=skipped_tests,
                    severity="low",
                )
            )

        return smells
