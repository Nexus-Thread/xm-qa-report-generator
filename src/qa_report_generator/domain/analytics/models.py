"""Domain models for analytics insights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.domain.models import Failure
    from qa_report_generator.domain.value_objects import TestIdentifier


@dataclass(frozen=True)
class TestPattern:
    """Detected testing pattern for reporting."""

    pattern_type: str
    description: str
    affected_tests: list[str]
    severity: str
    recommendation: str


@dataclass(frozen=True)
class FailureCluster:
    """Cluster of similar failures."""

    representative: Failure
    failures: list[Failure]
    count: int


@dataclass(frozen=True)
class TestTiming:
    """Timing information for a test."""

    test_name: str
    suite: str
    duration_seconds: float


@dataclass(frozen=True)
class HealthMetrics:
    """Aggregated health metrics for a test run."""

    average_duration_seconds: float | None
    slowest_tests: list[TestTiming]
    tests_by_module: dict[str, int]
    pass_rate_by_module: dict[str, float]
    flaky_tests: list[str]


@dataclass(frozen=True)
class QualityScore:
    """Overall quality score for a test run."""

    score: int
    factors: dict[str, float]


@dataclass(frozen=True)
class TestSmell:
    """Detected test smell for a test run."""

    smell_type: str
    description: str
    affected_tests: list[str]
    severity: str


@dataclass(frozen=True)
class ReportDiff:
    """Diff summary between two test runs."""

    new_failures: list[TestIdentifier]
    fixed_tests: list[TestIdentifier]
    regressions: list[TestIdentifier]
    total_previous: int
    total_current: int
