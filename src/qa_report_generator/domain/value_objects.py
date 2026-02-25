"""Domain value objects."""

from __future__ import annotations

from enum import Enum, StrEnum
from typing import NewType

from pydantic import BaseModel, Field, field_validator

TestName = NewType("TestName", str)
SuiteName = NewType("SuiteName", str)


class TestStatus(StrEnum):
    """Possible outcomes of a test execution."""

    __test__ = False

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class SectionType(StrEnum):
    """Types of narrative sections in generated reports."""

    EXECUTIVE_SUMMARY = "executive_summary"
    KEY_OBSERVATIONS = "key_observations"
    RISK_ASSESSMENT = "risk_assessment"
    RECOMMENDATION = "recommendation"


class Duration(BaseModel):
    """Time duration with formatted output."""

    SECONDS_PER_MINUTE: float = 60.0  # Formatting threshold

    seconds: float = Field(ge=0, description="Duration in seconds")

    @property
    def milliseconds(self) -> float:
        """Get duration in milliseconds."""
        return self.seconds * 1000

    @property
    def formatted(self) -> str:
        """Get human-readable formatted duration."""
        if self.seconds < 1:
            return f"{self.milliseconds:.0f}ms"
        if self.seconds < self.SECONDS_PER_MINUTE:
            return f"{self.seconds:.2f}s"
        minutes = int(self.seconds // self.SECONDS_PER_MINUTE)
        remaining_seconds = self.seconds % self.SECONDS_PER_MINUTE
        return f"{minutes}m {remaining_seconds:.1f}s"

    def __str__(self) -> str:
        """Return string representation."""
        return self.formatted


class PassRate(BaseModel):
    """Test pass rate with quality thresholds."""

    ACCEPTABLE_THRESHOLD: float = 95.0  # Pass rate considered healthy
    CRITICAL_THRESHOLD: float = 80.0  # Pass rate considered critical

    percentage: float = Field(ge=0, le=100, description="Pass rate as percentage")

    @classmethod
    def from_counts(cls, passed: int, total: int) -> PassRate:
        """Calculate pass rate from test counts."""
        if total == 0:
            return cls(percentage=0.0)
        return cls(percentage=(passed / total) * 100)

    @property
    def is_acceptable(self) -> bool:
        """Check if pass rate meets acceptable threshold."""
        return self.percentage >= self.ACCEPTABLE_THRESHOLD

    @property
    def is_critical(self) -> bool:
        """Check if pass rate is critically low."""
        return self.percentage < self.CRITICAL_THRESHOLD

    @property
    def formatted(self) -> str:
        """Get formatted pass rate string."""
        return f"{self.percentage:.1f}%"

    def __str__(self) -> str:
        """Return string representation."""
        return self.formatted


class TestIdentifier(BaseModel):
    """Unique identifier for a test case."""

    name: str = Field(min_length=1, description="Test method/function name")
    suite: str = Field(min_length=1, description="Test suite or module path")
    __test__ = False

    @property
    def full_name(self) -> str:
        """Get fully qualified test name."""
        return f"{self.suite}::{self.name}"

    @field_validator("name", "suite")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate that identifier parts are not empty or whitespace."""
        if not v.strip():
            msg = "Test identifier cannot be empty or whitespace"
            raise ValueError(msg)
        return v.strip()

    def __str__(self) -> str:
        """Return string representation."""
        return self.full_name

    def __hash__(self) -> int:
        """Make hashable for use in sets/dicts."""
        return hash((self.name, self.suite))


class FailureSeverity(Enum):
    """Severity tiers for failed tests."""

    LOW = 25
    MEDIUM = 50
    HIGH = 75
    CRITICAL = 100

    @property
    def score(self) -> int:
        """Return numeric score for prioritization."""
        return self.value
