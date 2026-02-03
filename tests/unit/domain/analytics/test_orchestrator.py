"""Unit tests for AnalyticsOrchestrator."""

from qa_report_generator.domain.analytics.orchestrator import AnalyticsOrchestrator
from qa_report_generator.domain.models import EnvironmentMeta, ReportFacts, RunMetrics
from qa_report_generator.domain.value_objects import Duration


def test_build_report_facts_populates_analytics() -> None:
    """Build report facts with populated analytics results."""
    orchestrator = AnalyticsOrchestrator()
    metrics = RunMetrics(
        total=2,
        passed=1,
        failed=1,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=[],
    )

    facts = orchestrator.build_report_facts(
        metrics=metrics,
        environment=EnvironmentMeta(env="test", build=None, commit=None, target_url=None),
        input_files=["report.json"],
        failure_clustering_threshold=0.7,
    )

    assert isinstance(facts, ReportFacts)
    assert facts.metrics == metrics
    assert facts.environment.env == "test"
    assert facts.input_files == ["report.json"]
    assert facts.patterns is not None
    assert facts.health_metrics is not None
    assert facts.quality_score is not None
    assert facts.test_smells is not None
