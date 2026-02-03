"""Analytics orchestration service."""

from __future__ import annotations

from qa_report_generator.domain.analytics import (
    FailureClusterer,
    FlakinessDetector,
    HealthMetricsCalculator,
    PatternDetector,
    QualityScoreCalculator,
    TestSmellDetector,
)
from qa_report_generator.domain.models import EnvironmentMeta, ReportFacts, RunMetrics


class AnalyticsOrchestrator:
    """Coordinate analytics calculators to build report facts."""

    def __init__(self) -> None:
        """Initialize analytics calculators."""
        self._pattern_detector = PatternDetector()
        self._flakiness_detector = FlakinessDetector()
        self._health_metrics_calculator = HealthMetricsCalculator()
        self._failure_clusterer = FailureClusterer()
        self._quality_score_calculator = QualityScoreCalculator()
        self._test_smell_detector = TestSmellDetector()

    def build_report_facts(
        self,
        *,
        metrics: RunMetrics,
        environment: EnvironmentMeta,
        input_files: list[str],
        failure_clustering_threshold: float,
    ) -> ReportFacts:
        """Create report facts with computed analytics."""
        patterns = self._pattern_detector.detect_patterns(metrics)
        flaky_tests = self._flakiness_detector.detect_flaky_tests(metrics)
        health_metrics = self._health_metrics_calculator.calculate(metrics, flaky_tests)
        quality_score = self._quality_score_calculator.calculate(
            pass_rate=metrics.pass_rate,
            flaky_tests=flaky_tests,
            max_failure_duration=max(
                (failure.duration.seconds for failure in metrics.failures if failure.duration),
                default=None,
            ),
        )
        test_smells = self._test_smell_detector.detect(metrics)
        failure_clusters = self._failure_clusterer.cluster_by_message_similarity(
            metrics.failures,
            threshold=failure_clustering_threshold,
        )

        return ReportFacts(
            metrics=metrics,
            environment=environment,
            input_files=input_files,
            patterns=patterns,
            health_metrics=health_metrics,
            failure_clusters=failure_clusters,
            quality_score=quality_score,
            test_smells=test_smells,
        )
