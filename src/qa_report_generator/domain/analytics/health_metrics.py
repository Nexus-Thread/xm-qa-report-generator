"""Health metrics calculations for test runs."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from qa_report_generator.domain.analytics.models import HealthMetrics, TestTiming

if TYPE_CHECKING:
    from qa_report_generator.domain.models import RunMetrics


class HealthMetricsCalculator:
    """Compute health metrics for a test run."""

    def calculate(self, metrics: RunMetrics, flaky_tests: list[str]) -> HealthMetrics:
        """Calculate health metrics based on run data."""
        duration_values = [result.duration.seconds for result in metrics.test_results if result.duration is not None]
        average_duration = sum(duration_values) / len(duration_values) if duration_values else None

        slowest_tests = sorted(
            [
                TestTiming(
                    test_name=result.test_name,
                    suite=result.suite,
                    duration_seconds=result.duration.seconds,
                )
                for result in metrics.test_results
                if result.duration is not None
            ],
            key=lambda timing: timing.duration_seconds,
            reverse=True,
        )[:5]

        tests_by_module: dict[str, int] = defaultdict(int)
        pass_rate_by_module: dict[str, float] = {}
        module_totals: dict[str, int] = defaultdict(int)
        module_passed: dict[str, int] = defaultdict(int)

        for result in metrics.test_results:
            tests_by_module[result.suite] += 1
            module_totals[result.suite] += 1
            if result.status.value == "passed":
                module_passed[result.suite] += 1

        for suite, total in module_totals.items():
            passed = module_passed.get(suite, 0)
            pass_rate_by_module[suite] = (passed / total) * 100 if total else 0.0

        return HealthMetrics(
            average_duration_seconds=average_duration,
            slowest_tests=slowest_tests,
            tests_by_module=dict(tests_by_module),
            pass_rate_by_module=pass_rate_by_module,
            flaky_tests=flaky_tests,
        )
