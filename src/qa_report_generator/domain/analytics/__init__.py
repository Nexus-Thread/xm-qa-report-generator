"""Domain analytics for report summarization."""

from qa_report_generator.domain.analytics.failure_clustering import FailureClusterer
from qa_report_generator.domain.analytics.flakiness_detector import FlakinessDetector
from qa_report_generator.domain.analytics.health_metrics import HealthMetricsCalculator
from qa_report_generator.domain.analytics.models import (
    FailureCluster,
    HealthMetrics,
    QualityScore,
    ReportDiff,
    TestPattern,
    TestSmell,
    TestTiming,
)
from qa_report_generator.domain.analytics.pattern_detector import PatternDetector
from qa_report_generator.domain.analytics.quality_metrics import QualityScoreCalculator
from qa_report_generator.domain.analytics.report_diff import diff_runs
from qa_report_generator.domain.analytics.test_smells import TestSmellDetector

__all__ = [
    "FailureCluster",
    "FailureClusterer",
    "FlakinessDetector",
    "HealthMetrics",
    "HealthMetricsCalculator",
    "PatternDetector",
    "QualityScore",
    "QualityScoreCalculator",
    "ReportDiff",
    "TestPattern",
    "TestSmell",
    "TestSmellDetector",
    "TestTiming",
    "diff_runs",
]
