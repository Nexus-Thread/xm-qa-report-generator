"""Analytics orchestration service."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.domain.analytics import (
    FailureClusterer,
    FlakinessDetector,
    HealthMetricsCalculator,
    PatternDetector,
    QualityScoreCalculator,
    TestSmellDetector,
)
from qa_report_generator.domain.models import EnvironmentMeta, ReportFacts, RunMetrics

if TYPE_CHECKING:
    from qa_report_generator.domain.models.performance import K6ReportContext


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

    def build_report_facts(  # noqa: PLR0913
        self,
        *,
        metrics: RunMetrics,
        environment: EnvironmentMeta,
        input_files: list[str],
        failure_clustering_threshold: float,
        source_format: str = "pytest",
        k6_context: K6ReportContext | None = None,
    ) -> ReportFacts:
        """Create report facts with computed analytics.

        Args:
            metrics: Parsed test run metrics
            environment: Environment metadata
            input_files: Source files processed
            failure_clustering_threshold: Similarity threshold for failure clustering
            source_format: Format identifier used to select applicable analytics
            k6_context: k6-specific check and threshold breakdown; None for non-k6 formats

        Returns:
            ReportFacts populated with all applicable analytics results

        """
        patterns = self._pattern_detector.detect_patterns(metrics)

        # Flakiness detection and test smells are not meaningful for k6 reports:
        # k6 has no test name conventions or captured output that these rely on.
        if source_format == "k6":
            flaky_tests: list[str] = []
            test_smells = []
        else:
            flaky_tests = self._flakiness_detector.detect_flaky_tests(metrics)
            test_smells = self._test_smell_detector.detect(metrics)

        health_metrics = self._health_metrics_calculator.calculate(metrics, flaky_tests)
        quality_score = self._quality_score_calculator.calculate(
            pass_rate=metrics.pass_rate,
            flaky_tests=flaky_tests,
            max_failure_duration=max(
                (failure.duration.seconds for failure in metrics.failures if failure.duration),
                default=None,
            ),
        )
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
            k6_context=k6_context,
        )
