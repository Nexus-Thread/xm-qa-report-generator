"""Unit tests for domain exception contracts."""

from __future__ import annotations

from qa_report_generator.domain import ReportingError


def test_reporting_error_str_returns_message() -> None:
    """ReportingError string conversion returns the message."""
    error = ReportingError("invalid report", suggestion="Check the input payload")

    assert str(error) == "invalid report"
    assert error.suggestion == "Check the input payload"
