"""Quality score calculation for test runs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.domain.analytics.models import QualityScore

if TYPE_CHECKING:
    from qa_report_generator.domain.value_objects import PassRate


class QualityScoreCalculator:
    """Compute an overall quality score for a test run."""

    def calculate(
        self,
        *,
        pass_rate: PassRate,
        flaky_tests: list[str],
        max_failure_duration: float | None,
    ) -> QualityScore:
        """Calculate a quality score and factors."""
        pass_rate_penalty = max(0.0, 100 - pass_rate.percentage) * 0.6
        flaky_penalty = min(25.0, len(flaky_tests) * 5.0)

        if max_failure_duration is None or max_failure_duration <= 5:
            slow_failure_penalty = 0.0
        elif max_failure_duration <= 15:
            slow_failure_penalty = 7.5
        else:
            slow_failure_penalty = 15.0

        score = max(0, round(100 - pass_rate_penalty - flaky_penalty - slow_failure_penalty))
        return QualityScore(
            score=score,
            factors={
                "pass_rate_penalty": round(pass_rate_penalty, 2),
                "flaky_penalty": round(flaky_penalty, 2),
                "slow_failure_penalty": round(slow_failure_penalty, 2),
            },
        )
