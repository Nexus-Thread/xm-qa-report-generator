"""Unit tests for failure preprocessing utilities."""

from __future__ import annotations

from qa_report_generator.domain.models import Failure, TestOutput
from qa_report_generator.domain.preprocessors import (
    FailureGrouper,
    FailurePatternExtractor,
    OutputTruncator,
)
from qa_report_generator.domain.value_objects import TestIdentifier


def test_output_truncator_returns_none_when_output_is_empty() -> None:
    """Return None when no output is provided."""
    truncator = OutputTruncator(max_head_lines=2, max_tail_lines=2)

    assert truncator.truncate_output(None) is None


def test_output_truncator_keeps_short_output() -> None:
    """Avoid truncation when output is within limits."""
    output = TestOutput(stdout="line1\nline2", stderr=None, log=None)
    truncator = OutputTruncator(max_head_lines=2, max_tail_lines=2)

    truncated = truncator.truncate_output(output)

    assert truncated
    assert truncated.stdout == "line1\nline2"


def test_output_truncator_truncates_long_output() -> None:
    """Truncate output while preserving head and tail lines."""
    output = TestOutput(stdout="\n".join(f"line{i}" for i in range(8)), stderr=None, log=None)
    truncator = OutputTruncator(max_head_lines=2, max_tail_lines=2)

    truncated = truncator.truncate_output(output)

    assert truncated
    assert truncated.stdout
    assert "line0" in truncated.stdout
    assert "line1" in truncated.stdout
    assert "line6" in truncated.stdout
    assert "line7" in truncated.stdout
    assert "... (truncated 4 lines) ..." in truncated.stdout


def test_output_truncator_truncates_with_no_tail() -> None:
    """Truncate output when only head lines are kept."""
    output = TestOutput(stdout="\n".join(f"line{i}" for i in range(6)), stderr=None, log=None)
    truncator = OutputTruncator(max_head_lines=2, max_tail_lines=0)

    truncated = truncator.truncate_output(output)

    assert truncated
    assert truncated.stdout
    assert "line0" in truncated.stdout
    assert "line1" in truncated.stdout
    assert "... (truncated 4 lines) ..." in truncated.stdout


def test_pattern_extractor_normalizes_message_and_type() -> None:
    """Normalize URLs and paths in failure signatures."""
    failure = Failure(
        identifier=TestIdentifier(name="test_api", suite="tests.api"),
        message="Failed for https://example.com/users/42 at /tmp/logs/error.log",
        type="AssertionError",
        duration=None,
        output=None,
    )
    extractor = FailurePatternExtractor()

    signature = extractor.signature_for_failure(failure)

    assert signature.startswith("AssertionError:")
    assert "<url>" in signature
    assert "<path>" in signature


def test_failure_grouper_groups_by_signature() -> None:
    """Group failures with identical signatures together."""
    failures = [
        Failure(
            identifier=TestIdentifier(name="test_one", suite="tests.api"),
            message="Expected 200 got 500",
            type="AssertionError",
            duration=None,
            output=None,
        ),
        Failure(
            identifier=TestIdentifier(name="test_two", suite="tests.api"),
            message="Expected 200 got 500",
            type="AssertionError",
            duration=None,
            output=None,
        ),
        Failure(
            identifier=TestIdentifier(name="test_three", suite="tests.api"),
            message="Connection timed out",
            type="TimeoutError",
            duration=None,
            output=None,
        ),
    ]

    groups = FailureGrouper().group_failures_by_pattern(failures)

    assert len(groups) == 2
    assertion_group = next(group for group in groups if group.count == 2)
    assert assertion_group.test_names == ["test_one", "test_two"]
