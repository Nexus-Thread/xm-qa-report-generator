"""Test run metrics model."""

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from qa_report_generator.domain.models.failure import Failure
from qa_report_generator.domain.models.test_case import TestCaseResult
from qa_report_generator.domain.value_objects import Duration, FailureSeverity, PassRate

if TYPE_CHECKING:
    from qa_report_generator.domain.preprocessors import FailureGroup


class RunMetrics(BaseModel):
    """Aggregated metrics for a test run."""

    total: int = Field(ge=0, description="Total number of tests executed")
    passed: int = Field(ge=0, description="Number of tests that passed")
    failed: int = Field(ge=0, description="Number of tests that failed")
    skipped: int = Field(ge=0, description="Number of tests that were skipped")
    errors: int = Field(ge=0, default=0, description="Number of tests with errors")
    duration: Duration | None = Field(None, description="Total execution duration")
    failures: list[Failure] = Field(default_factory=list, description="Details of failed tests")
    test_results: list[TestCaseResult] = Field(
        default_factory=list,
        description="All test results for analytics",
    )

    @field_validator("failures")
    @classmethod
    def validate_failures_count(cls, failures: list[Failure], info: Any) -> list[Failure]:
        """Ensure failures list does not exceed total failed + errors."""
        data = info.data
        if not data:
            return failures
        total_failures = data.get("failed", 0) + data.get("errors", 0)
        if len(failures) > total_failures:
            msg = f"Failures list cannot exceed total failed + errors ({total_failures})."
            raise ValueError(msg)
        return failures

    @field_validator("passed", "failed", "skipped", "errors")
    @classmethod
    def validate_counts(cls, v: int, info: Any) -> int:
        """Validate that counts are non-negative."""
        if v < 0:
            msg = f"{info.field_name} must be non-negative"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_counts_sum(self) -> "RunMetrics":
        """Validate that counts sum to total."""
        expected_total = self.passed + self.failed + self.skipped + self.errors
        if self.total != expected_total:
            msg = (
                f"Total tests ({self.total}) must equal sum of passed ({self.passed}) + "
                f"failed ({self.failed}) + skipped ({self.skipped}) + errors ({self.errors}) = {expected_total}"
            )
            raise ValueError(msg)
        return self

    @property
    def pass_rate(self) -> PassRate:
        """Calculate pass rate as a value object."""
        return PassRate.from_counts(self.passed, self.total)

    @property
    def duration_seconds(self) -> float | None:
        """Get duration in seconds for backward compatibility."""
        return self.duration.seconds if self.duration else None

    def has_failures(self) -> bool:
        """Check if there are any failures or errors."""
        return self.failed > 0 or self.errors > 0

    def is_healthy(self) -> bool:
        """Check if test run is healthy."""
        return self.pass_rate.is_acceptable

    def limit_failures(self, max_failures: int) -> "RunMetrics":
        """Create a new RunMetrics with a limited failure list.

        Args:
            max_failures: Maximum number of failures to include

        Returns:
            New RunMetrics instance with truncated failures

        """
        if max_failures < 0:
            msg = "max_failures must be non-negative"
            raise ValueError(msg)

        if len(self.failures) <= max_failures:
            return self

        sorted_failures = sorted(
            self.failures,
            key=self._failure_priority_score,
            reverse=True,
        )

        return RunMetrics(
            total=self.total,
            passed=self.passed,
            failed=self.failed,
            skipped=self.skipped,
            errors=self.errors,
            duration=self.duration,
            failures=sorted_failures[:max_failures],
            test_results=self.test_results,
        )

    def group_failures_by_pattern(self) -> list["FailureGroup"]:
        """Group failures by error signature."""
        from qa_report_generator.domain.preprocessors import FailureGrouper

        return FailureGrouper().group_failures_by_pattern(self.failures)

    def _failure_priority_score(self, failure: Failure) -> int:
        """Score failures by severity."""
        score = FailureSeverity.MEDIUM.score
        lowered_name = failure.test_name.lower()

        if "critical" in lowered_name:
            score += 25
        if "flaky" in lowered_name or "random" in lowered_name:
            score -= 10

        error_type = (failure.type or "").lower()
        if error_type in {"systemerror", "memoryerror", "keyerror"}:
            score += 20
        if error_type in {"assertionerror", "assert"}:
            score -= 5

        if failure.duration and failure.duration.seconds > 10:
            score += 10

        return max(score, FailureSeverity.LOW.score)
