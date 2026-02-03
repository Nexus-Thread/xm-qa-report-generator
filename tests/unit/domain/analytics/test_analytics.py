"""Unit tests for analytics modules."""

from __future__ import annotations

from qa_report_generator.domain.analytics.failure_clustering import FailureClusterer
from qa_report_generator.domain.analytics.flakiness_detector import FlakinessDetector
from qa_report_generator.domain.analytics.health_metrics import HealthMetricsCalculator
from qa_report_generator.domain.analytics.pattern_detector import PatternDetector
from qa_report_generator.domain.analytics.quality_metrics import QualityScoreCalculator
from qa_report_generator.domain.analytics.test_smells import TestSmellDetector
from qa_report_generator.domain.models import Failure, RunMetrics, TestCaseResult
from qa_report_generator.domain.value_objects import Duration, TestIdentifier, TestStatus


def _build_failure(
    name: str,
    suite: str,
    message: str,
    error_type: str,
    duration_seconds: float | None = None,
) -> Failure:
    return Failure(
        identifier=TestIdentifier(name=name, suite=suite),
        message=message,
        type=error_type,
        duration=Duration(seconds=duration_seconds) if duration_seconds is not None else None,
        output=None,
    )


def _build_result(
    name: str,
    suite: str,
    status: TestStatus,
    duration_seconds: float | None = None,
) -> TestCaseResult:
    return TestCaseResult(
        identifier=TestIdentifier(name=name, suite=suite),
        status=status,
        duration=Duration(seconds=duration_seconds) if duration_seconds is not None else None,
    )


def test_pattern_detector_finds_common_error_types() -> None:
    """Detect common error patterns across failures."""
    failures = [
        _build_failure("test_one", "tests.api", "boom", "ValueError", 1.0),
        _build_failure("test_two", "tests.api", "boom", "ValueError", 2.0),
        _build_failure("test_three", "tests.api", "boom", "ValueError", 3.0),
    ]
    metrics = RunMetrics(
        total=3,
        passed=0,
        failed=3,
        skipped=0,
        errors=0,
        duration=Duration(seconds=3.0),
        failures=failures,
        test_results=[],
    )

    patterns = PatternDetector(minimum_group_size=3).detect_patterns(metrics)

    assert any(pattern.pattern_type == "common_error" for pattern in patterns)


def test_flakiness_detector_flags_name_and_timeout_message() -> None:
    """Flag tests as flaky using names and timeout message heuristics."""
    failures = [
        _build_failure("test_random_pick", "tests.api", "boom", "ValueError"),
        _build_failure("test_slow", "tests.api", "Request timed out", "TimeoutError"),
    ]
    metrics = RunMetrics(
        total=2,
        passed=0,
        failed=2,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=failures,
        test_results=[],
    )

    flaky = FlakinessDetector().detect_flaky_tests(metrics)

    assert "test_random_pick" in flaky
    assert "test_slow" in flaky


def test_failure_clusterer_groups_similar_messages() -> None:
    """Cluster similar failure messages together."""
    failures = [
        _build_failure("test_one", "tests.api", "DB connection failed", "Error"),
        _build_failure("test_two", "tests.api", "DB connection failed", "Error"),
        _build_failure("test_three", "tests.api", "Auth failed", "Error"),
    ]

    clusters = FailureClusterer().cluster_by_message_similarity(failures, threshold=0.7)

    assert any(cluster.count == 2 for cluster in clusters)


def test_health_metrics_uses_test_results_for_pass_rate() -> None:
    """Compute pass rate using the per-test results list."""
    test_results = [
        _build_result("test_one", "tests.api", TestStatus.PASSED, 1.2),
        _build_result("test_two", "tests.api", TestStatus.FAILED, 2.2),
        _build_result("test_three", "tests.api", TestStatus.PASSED, 0.8),
    ]
    metrics = RunMetrics(
        total=3,
        passed=2,
        failed=1,
        skipped=0,
        errors=0,
        duration=Duration(seconds=4.2),
        failures=[],
        test_results=test_results,
    )

    health = HealthMetricsCalculator().calculate(metrics, flaky_tests=[])

    assert health.tests_by_module["tests.api"] == 3
    assert health.pass_rate_by_module["tests.api"] == (2 / 3) * 100


def test_quality_score_penalizes_low_pass_rate() -> None:
    """Lower pass rate should reduce quality score."""
    calculator = QualityScoreCalculator()
    score = calculator.calculate(
        pass_rate=RunMetrics(
            total=10,
            passed=5,
            failed=5,
            skipped=0,
            errors=0,
            duration=Duration(seconds=1.0),
            failures=[],
            test_results=[],
        ).pass_rate,
        flaky_tests=[],
        max_failure_duration=None,
    )

    assert score.score < 100


def test_test_smell_detector_flags_long_tests() -> None:
    """Long-running tests should be flagged as a test smell."""
    test_results = [
        _build_result("test_slow", "tests.api", TestStatus.PASSED, 45.0),
        _build_result("test_fast", "tests.api", TestStatus.PASSED, 1.0),
    ]
    metrics = RunMetrics(
        total=2,
        passed=2,
        failed=0,
        skipped=0,
        errors=0,
        duration=Duration(seconds=46.0),
        failures=[],
        test_results=test_results,
    )

    smells = TestSmellDetector().detect(metrics)

    assert any(smell.smell_type == "long_running" for smell in smells)
