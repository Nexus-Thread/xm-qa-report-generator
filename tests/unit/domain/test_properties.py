"""Property-based tests for domain validation rules."""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from qa_report_generator.domain.models import RunMetrics, TestOutput
from qa_report_generator.domain.value_objects import Duration, PassRate, TestIdentifier


@given(st.text())
def test_test_identifier_trims_and_rejects_blank(values: str) -> None:
    """TestIdentifier strips whitespace and rejects blank values."""
    if values.strip():
        identifier = TestIdentifier(name=values, suite=values)
        assert identifier.name == values.strip()
        assert identifier.suite == values.strip()
    else:
        with pytest.raises(ValidationError):
            TestIdentifier(name=values, suite=values)


@given(st.floats(min_value=0, max_value=10_000, allow_nan=False, allow_infinity=False))
def test_duration_formats_non_negative(seconds: float) -> None:
    """Duration always formats non-negative durations."""
    duration = Duration(seconds=seconds)
    assert duration.seconds >= 0
    assert duration.formatted


@given(
    st.integers(min_value=0, max_value=500),
    st.integers(min_value=0, max_value=500),
    st.integers(min_value=0, max_value=500),
    st.integers(min_value=0, max_value=500),
)
def test_run_metrics_requires_total_sum(
    passed: int,
    failed: int,
    skipped: int,
    errors: int,
) -> None:
    """RunMetrics enforces total == passed + failed + skipped + errors."""
    total = passed + failed + skipped + errors
    metrics = RunMetrics(
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        errors=errors,
        duration=Duration(seconds=0.1),
    )

    assert metrics.total == total
    assert metrics.pass_rate.percentage == PassRate.from_counts(passed, total).percentage


@given(st.text())
def test_test_output_normalizes_blank_streams(value: str) -> None:
    """TestOutput normalizes blank/whitespace-only streams to None."""
    output = TestOutput(stdout=value, stderr=value, log=value)
    if value.strip():
        assert output.stdout == value.rstrip()
        assert output.stderr == value.rstrip()
        assert output.log == value.rstrip()
    else:
        assert output.stdout is None
        assert output.stderr is None
        assert output.log is None
