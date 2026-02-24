"""Report facts aggregate model."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from qa_report_generator.domain.analytics.models import (
    FailureCluster,
    HealthMetrics,
    QualityScore,
    TestPattern,
    TestSmell,
)
from qa_report_generator.domain.models.common.environment import EnvironmentMeta
from qa_report_generator.domain.models.common.failure import Failure
from qa_report_generator.domain.models.common.metrics import RunMetrics


class ReportFacts(BaseModel):
    """Complete test run data for report generation."""

    metrics: RunMetrics = Field(description="Test run metrics and results")
    environment: EnvironmentMeta = Field(description="Environment metadata")
    input_files: list[str] = Field(description="Source files processed")
    source_format: str = Field(default="pytest", description="Report source format identifier (e.g. pytest, k6)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Report generation time")
    patterns: list[TestPattern] = Field(default_factory=list, description="Detected failure patterns")
    health_metrics: HealthMetrics | None = Field(default=None, description="Aggregated test suite health metrics")
    failure_clusters: list[FailureCluster] = Field(
        default_factory=list,
        description="Failure clusters for summarization",
    )
    quality_score: QualityScore | None = Field(default=None, description="Overall test suite quality score")
    test_smells: list[TestSmell] = Field(default_factory=list, description="Detected test smells")

    @property
    def timestamp_iso(self) -> str:
        """Get timestamp in ISO 8601 format."""
        return self.timestamp.isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "metrics": {
                "total": self.metrics.total,
                "passed": self.metrics.passed,
                "failed": self.metrics.failed,
                "skipped": self.metrics.skipped,
                "errors": self.metrics.errors,
                "duration_seconds": self.metrics.duration_seconds,
                "pass_rate": self.metrics.pass_rate.formatted,
                "failures": [
                    {
                        "test_name": f.identifier.name,
                        "suite": f.identifier.suite,
                        "message": f.message,
                        "type": f.type,
                        "duration_seconds": f.duration.seconds if f.duration else None,
                    }
                    for f in self.metrics.failures
                ],
            },
            "patterns": [
                {
                    "type": pattern.pattern_type,
                    "description": pattern.description,
                    "severity": pattern.severity,
                    "recommendation": pattern.recommendation,
                    "affected_tests": pattern.affected_tests,
                }
                for pattern in self.patterns
            ],
            "health_metrics": (
                {
                    "average_duration_seconds": self.health_metrics.average_duration_seconds,
                    "slowest_tests": [
                        {
                            "test_name": timing.test_name,
                            "suite": timing.suite,
                            "duration_seconds": timing.duration_seconds,
                        }
                        for timing in self.health_metrics.slowest_tests
                    ],
                    "tests_by_module": self.health_metrics.tests_by_module,
                    "pass_rate_by_module": self.health_metrics.pass_rate_by_module,
                    "flaky_tests": self.health_metrics.flaky_tests,
                }
                if self.health_metrics
                else None
            ),
            "quality_score": (
                {
                    "score": self.quality_score.score,
                    "factors": self.quality_score.factors,
                }
                if self.quality_score
                else None
            ),
            "test_smells": [
                {
                    "type": smell.smell_type,
                    "description": smell.description,
                    "severity": smell.severity,
                    "affected_tests": smell.affected_tests,
                }
                for smell in self.test_smells
            ],
            "failure_clusters": [
                {
                    "count": cluster.count,
                    "representative": {
                        "test_name": cluster.representative.test_name,
                        "suite": cluster.representative.suite,
                        "message": cluster.representative.message,
                        "type": cluster.representative.type,
                        "duration_seconds": (cluster.representative.duration.seconds if cluster.representative.duration else None),
                    },
                    "sample_tests": [failure.test_name for failure in cluster.failures[:5]],
                }
                for cluster in self.failure_clusters
            ],
            "environment": self.environment.model_dump(),
            "input_files": self.input_files,
            "source_format": self.source_format,
            "timestamp": self.timestamp_iso,
        }


ReportFacts.model_rebuild(
    _types_namespace={
        "Failure": Failure,
        "FailureCluster": FailureCluster,
        "HealthMetrics": HealthMetrics,
        "QualityScore": QualityScore,
        "TestSmell": TestSmell,
        "TestPattern": TestPattern,
    },
)
