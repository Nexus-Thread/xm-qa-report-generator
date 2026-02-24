"""Unit tests for domain models and value objects."""

from __future__ import annotations

import pytest

from qa_report_generator.domain.models import (
    EnvironmentMeta,
    Failure,
    RunMetrics,
    TestOutput,
)
from qa_report_generator.domain.value_objects import Duration, TestIdentifier


def test_test_output_normalizes_empty_and_trailing_whitespace() -> None:
    """Ensure output fields are trimmed and blank values become None."""
    output = TestOutput(stdout="hello  \n", stderr="\n", log=None)

    assert output.stdout == "hello"
    assert output.stderr is None
    assert output.log is None


def test_environment_meta_defaults_to_all_none() -> None:
    """All fields default to None when omitted."""
    meta = EnvironmentMeta()

    assert meta.env is None
    assert meta.build is None
    assert meta.commit is None
    assert meta.target_url is None


def test_environment_meta_preserves_valid_values() -> None:
    """Clean, non-empty values are returned unchanged."""
    meta = EnvironmentMeta(env="staging", build="123", commit="abc123", target_url="https://example.com")

    assert meta.env == "staging"
    assert meta.build == "123"
    assert meta.commit == "abc123"
    assert meta.target_url == "https://example.com"


def test_environment_meta_trims_and_nulls_empty_values() -> None:
    """Ensure optional environment metadata is normalized."""
    meta = EnvironmentMeta(env=" staging ", build=" ", commit=None, target_url="")

    assert meta.env == "staging"
    assert meta.build is None
    assert meta.commit is None
    assert meta.target_url is None


def test_run_metrics_rejects_failures_exceeding_failed_count() -> None:
    """Reject failure lists larger than the failed+error counts."""
    identifier = TestIdentifier(name="test_example", suite="tests.test_example")
    failure = Failure(identifier=identifier, message="boom", type=None, duration=None, output=None)

    with pytest.raises(ValueError, match="Failures list cannot exceed"):
        RunMetrics(
            total=1,
            passed=0,
            failed=0,
            skipped=0,
            errors=0,
            duration=Duration(seconds=1.0),
            failures=[failure],
        )


def test_run_metrics_limit_failures_rejects_negative() -> None:
    """Reject negative failure limits to preserve invariants."""
    metrics = RunMetrics(
        total=1,
        passed=1,
        failed=0,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=[],
    )

    with pytest.raises(ValueError, match="max_failures must be non-negative"):
        metrics.limit_failures(-1)


def test_run_metrics_limit_failures_prioritizes_critical_failures() -> None:
    """Prioritize critical failures when limiting the failure list."""
    critical_failure = Failure(
        identifier=TestIdentifier(name="test_critical_path", suite="tests.critical"),
        message="boom",
        type="SystemError",
        duration=Duration(seconds=12.0),
        output=None,
    )
    regular_failure = Failure(
        identifier=TestIdentifier(name="test_regular", suite="tests.regular"),
        message="assert failed",
        type="AssertionError",
        duration=Duration(seconds=0.3),
        output=None,
    )

    metrics = RunMetrics(
        total=2,
        passed=0,
        failed=2,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=[regular_failure, critical_failure],
    )

    limited = metrics.limit_failures(1)

    assert limited.failures == [critical_failure]


def test_run_metrics_limit_failures_prioritizes_longer_failures_over_flaky() -> None:
    """Long-running failures should outrank flaky/random tests."""
    flaky_failure = Failure(
        identifier=TestIdentifier(name="test_flaky_random", suite="tests.flaky"),
        message="oops",
        type="AssertionError",
        duration=Duration(seconds=0.5),
        output=None,
    )
    slow_failure = Failure(
        identifier=TestIdentifier(name="test_slow_process", suite="tests.slow"),
        message="timeout",
        type="AssertionError",
        duration=Duration(seconds=15.0),
        output=None,
    )

    metrics = RunMetrics(
        total=2,
        passed=0,
        failed=2,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=[flaky_failure, slow_failure],
    )

    limited = metrics.limit_failures(1)

    assert limited.failures == [slow_failure]
