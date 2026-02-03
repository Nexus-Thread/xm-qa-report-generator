"""Pattern detection for test failures and suite health."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from qa_report_generator.domain.analytics.models import TestPattern

if TYPE_CHECKING:
    from qa_report_generator.domain.models import RunMetrics


class PatternDetector:
    """Detect common failure patterns in test runs."""

    def __init__(self, minimum_group_size: int = 3) -> None:
        """Initialize detector thresholds."""
        self.minimum_group_size = minimum_group_size

    def detect_patterns(self, metrics: RunMetrics) -> list[TestPattern]:
        """Detect patterns from run metrics."""
        patterns: list[TestPattern] = []
        patterns.extend(self._detect_common_error_types(metrics))
        patterns.extend(self._detect_module_failures(metrics))
        patterns.extend(self._detect_temporal_concentration(metrics))
        return patterns

    def _detect_common_error_types(self, metrics: RunMetrics) -> list[TestPattern]:
        failures = metrics.failures
        counter = Counter((failure.type or "UnknownError") for failure in failures)
        patterns: list[TestPattern] = []
        for error_type, count in counter.items():
            if count < self.minimum_group_size:
                continue
            affected_tests = [failure.test_name for failure in failures if (failure.type or "UnknownError") == error_type]
            patterns.append(
                TestPattern(
                    pattern_type="common_error",
                    description=f"{count} tests failed with {error_type}",
                    affected_tests=affected_tests,
                    severity="high" if count >= 5 else "medium",
                    recommendation="Investigate shared root cause for the error type.",
                ),
            )
        return patterns

    def _detect_module_failures(self, metrics: RunMetrics) -> list[TestPattern]:
        failures = metrics.failures
        by_suite: dict[str, list[str]] = defaultdict(list)
        for failure in failures:
            by_suite[failure.suite].append(failure.test_name)

        patterns = []
        for suite, tests in by_suite.items():
            if len(tests) < self.minimum_group_size:
                continue
            patterns.append(
                TestPattern(
                    pattern_type="module_failure",
                    description=f"{len(tests)} failures in {suite}",
                    affected_tests=tests,
                    severity="high" if len(tests) >= 5 else "medium",
                    recommendation="Review recent changes in the module or shared fixtures.",
                ),
            )
        return patterns

    def _detect_temporal_concentration(self, metrics: RunMetrics) -> list[TestPattern]:
        failures = metrics.failures
        if len(failures) < self.minimum_group_size:
            return []

        durations = [failure.duration.seconds for failure in failures if failure.duration]
        if len(durations) < self.minimum_group_size:
            return []

        sorted_durations = sorted(durations)
        threshold_index = int(len(sorted_durations) * 0.7)
        threshold = sorted_durations[threshold_index]
        concentrated_failures = [failure for failure in failures if failure.duration and failure.duration.seconds >= threshold]
        if len(concentrated_failures) < self.minimum_group_size:
            return []

        return [
            TestPattern(
                pattern_type="temporal_concentration",
                description=(f"{len(concentrated_failures)} failures occurred among slower tests (>= {threshold:.2f}s)"),
                affected_tests=[failure.test_name for failure in concentrated_failures],
                severity="medium",
                recommendation="Investigate slow tests or resource contention near end of run.",
            ),
        ]
