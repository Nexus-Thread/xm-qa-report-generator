"""Heuristic detector for flaky tests."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.domain.models import Failure, RunMetrics


class FlakinessDetector:
    """Detect tests that appear flaky based on heuristics."""

    _name_patterns = [
        re.compile(r"test_random_", re.IGNORECASE),
        re.compile(r"test_race_", re.IGNORECASE),
        re.compile(r"flaky", re.IGNORECASE),
    ]
    _message_patterns = [
        re.compile(r"timeout", re.IGNORECASE),
        re.compile(r"timed out", re.IGNORECASE),
        re.compile(r"race condition", re.IGNORECASE),
    ]

    def detect_flaky_tests(self, metrics: RunMetrics) -> list[str]:
        """Return test names that appear flaky."""
        flaky_tests: set[str] = set()
        for failure in metrics.failures:
            if self._matches_failure(failure):
                flaky_tests.add(failure.test_name)
        return sorted(flaky_tests)

    def _matches_failure(self, failure: Failure) -> bool:
        name = failure.test_name
        if any(pattern.search(name) for pattern in self._name_patterns):
            return True
        message = failure.message
        return any(pattern.search(message) for pattern in self._message_patterns)
