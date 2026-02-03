"""Serialization utilities for LLM prompt payloads."""

from typing import Any

from qa_report_generator.domain.models import Failure, ReportFacts, TestOutput
from qa_report_generator.domain.preprocessors import FailureGroup, OutputTruncator


def build_llm_facts_payload(
    facts: ReportFacts,
    max_output_lines: int,
    enable_failure_grouping: bool,
    max_detailed_failures: int,
) -> dict[str, Any]:
    """Build a preprocessed facts payload optimized for LLM prompts.

    Args:
        facts: Test run facts
        max_output_lines: Maximum output lines per failure
        enable_failure_grouping: Whether to group similar failures
        max_detailed_failures: Maximum failures to include in detail

    Returns:
        Dictionary payload ready for JSON serialization

    """
    truncator = OutputTruncator(
        max_head_lines=max_output_lines,
        max_tail_lines=0,
    )

    return {
        "metrics": serialize_metrics(facts, truncator, enable_failure_grouping, max_detailed_failures),
        "patterns": serialize_patterns(facts),
        "health_metrics": serialize_health_metrics(facts),
        "quality_score": serialize_quality_score(facts),
        "test_smells": serialize_test_smells(facts),
        "failure_clusters": serialize_failure_clusters(facts),
        "environment": facts.environment.model_dump(),
        "input_files": facts.input_files,
        "timestamp": facts.timestamp_iso,
    }


def serialize_metrics(
    facts: ReportFacts,
    truncator: OutputTruncator,
    enable_failure_grouping: bool,
    max_detailed_failures: int,
) -> dict[str, Any]:
    """Serialize metrics with failure grouping and truncation.

    Args:
        facts: Test run facts
        truncator: Output truncator
        enable_failure_grouping: Whether to group similar failures
        max_detailed_failures: Maximum failures to include in detail

    Returns:
        Serialized metrics dictionary

    """
    failure_groups = build_failure_groups(facts, enable_failure_grouping)
    detailed_failures = facts.metrics.failures[:max_detailed_failures]

    return {
        "total": facts.metrics.total,
        "passed": facts.metrics.passed,
        "failed": facts.metrics.failed,
        "skipped": facts.metrics.skipped,
        "errors": facts.metrics.errors,
        "duration_seconds": facts.metrics.duration_seconds,
        "pass_rate": facts.metrics.pass_rate.formatted,
        "failures": [serialize_failure_group(group, truncator) for group in failure_groups],
        "detailed_failures": [serialize_detailed_failure(failure, truncator) for failure in detailed_failures],
    }


def serialize_patterns(facts: ReportFacts) -> list[dict[str, Any]]:
    """Serialize detected patterns.

    Args:
        facts: Test run facts

    Returns:
        List of serialized patterns

    """
    return [
        {
            "type": pattern.pattern_type,
            "description": pattern.description,
            "severity": pattern.severity,
            "recommendation": pattern.recommendation,
            "affected_tests": pattern.affected_tests[:10],
        }
        for pattern in facts.patterns
    ]


def serialize_quality_score(facts: ReportFacts) -> dict[str, Any] | None:
    """Serialize quality score.

    Args:
        facts: Test run facts

    Returns:
        Serialized quality score or None

    """
    if facts.quality_score is None:
        return None

    return {
        "score": facts.quality_score.score,
        "factors": facts.quality_score.factors,
    }


def serialize_test_smells(facts: ReportFacts) -> list[dict[str, Any]]:
    """Serialize test smells.

    Args:
        facts: Test run facts

    Returns:
        List of serialized test smells

    """
    return [
        {
            "type": smell.smell_type,
            "description": smell.description,
            "severity": smell.severity,
            "affected_tests": smell.affected_tests[:10],
        }
        for smell in facts.test_smells
    ]


def serialize_failure_clusters(facts: ReportFacts) -> list[dict[str, Any]]:
    """Serialize failure clusters.

    Args:
        facts: Test run facts

    Returns:
        List of serialized failure clusters

    """
    return [
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
        for cluster in facts.failure_clusters
    ]


def serialize_health_metrics(facts: ReportFacts) -> dict[str, Any] | None:
    """Serialize health metrics.

    Args:
        facts: Test run facts

    Returns:
        Serialized health metrics or None

    """
    metrics = facts.health_metrics
    if metrics is None:
        return None

    return {
        "average_duration_seconds": metrics.average_duration_seconds,
        "slowest_tests": [
            {
                "test_name": timing.test_name,
                "suite": timing.suite,
                "duration_seconds": timing.duration_seconds,
            }
            for timing in metrics.slowest_tests
        ],
        "tests_by_module": metrics.tests_by_module,
        "pass_rate_by_module": metrics.pass_rate_by_module,
        "flaky_tests": metrics.flaky_tests,
    }


def build_failure_groups(facts: ReportFacts, enable_failure_grouping: bool) -> list[FailureGroup]:
    """Build failure groups based on configuration.

    Args:
        facts: Test run facts
        enable_failure_grouping: Whether to group similar failures

    Returns:
        List of failure groups

    """
    if enable_failure_grouping:
        return facts.metrics.group_failures_by_pattern()

    return [
        FailureGroup(
            signature=f"{failure.type or 'UnknownError'}:{failure.message}",
            count=1,
            representative=failure,
            test_names=[failure.test_name],
        )
        for failure in facts.metrics.failures
    ]


def serialize_failure_group(
    group: FailureGroup,
    truncator: OutputTruncator,
) -> dict[str, Any]:
    """Serialize a failure group.

    Args:
        group: Failure group to serialize
        truncator: Output truncator

    Returns:
        Serialized failure group

    """
    representative = group.representative
    truncated_output = truncator.truncate_output(representative.output)

    return {
        "signature": group.signature,
        "count": group.count,
        "summary": format_failure_group_summary(group),
        "sample_tests": group.test_names[:5],
        "representative": {
            "test_name": representative.test_name,
            "suite": representative.suite,
            "message": representative.message,
            "type": representative.type,
            "duration_seconds": representative.duration.seconds if representative.duration else None,
            "output": serialize_output(truncated_output),
        },
    }


def format_failure_group_summary(group: FailureGroup) -> str:
    """Format a summary for a failure group.

    Args:
        group: Failure group

    Returns:
        Human-readable summary

    """
    representative = group.representative
    error_type = representative.type or "UnknownError"
    message = representative.message
    return f"{group.count} tests failed with {error_type}: {message}"


def serialize_detailed_failure(
    failure: Failure,
    truncator: OutputTruncator,
) -> dict[str, Any]:
    """Serialize a detailed failure.

    Args:
        failure: Failure to serialize
        truncator: Output truncator

    Returns:
        Serialized failure

    """
    truncated_output = truncator.truncate_output(failure.output)
    return {
        "test_name": failure.test_name,
        "suite": failure.suite,
        "message": failure.message,
        "type": failure.type,
        "duration_seconds": failure.duration.seconds if failure.duration else None,
        "output": serialize_output(truncated_output),
    }


def serialize_output(output: TestOutput | None) -> dict[str, str] | None:
    """Serialize test output, filtering empty values.

    Args:
        output: Test output to serialize

    Returns:
        Serialized output or None

    """
    if output is None:
        return None

    output_dict = {
        "stdout": output.stdout,
        "stderr": output.stderr,
        "log": output.log,
    }

    return {key: value for key, value in output_dict.items() if value}
