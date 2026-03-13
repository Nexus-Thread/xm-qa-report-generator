"""Focused tests for scenario verification helpers."""

from __future__ import annotations

from qa_report_generator_performance.application.dtos import VerificationMismatch
from qa_report_generator_performance.application.exceptions import ExtractionVerificationError
from qa_report_generator_performance.application.use_cases.k6_service_extraction.scenario_verification import (
    build_verification_error,
)


def test_build_verification_error_includes_stable_mismatch_details() -> None:
    """Verification errors should preserve stable first-mismatch context."""
    mismatch = VerificationMismatch(
        field="http_reqs.count",
        expected=100,
        actual=101,
        source_jsonpath="$.source.metrics.http_reqs.values.count",
        extracted_jsonpath="$.extracted.http_reqs.count",
        reason="value mismatch",
    )

    error = build_verification_error(mismatch)

    assert isinstance(error, ExtractionVerificationError)
    assert str(error) == (
        "Verification failed with numeric mismatches. First mismatch: http_reqs.count expected=100 actual=101 source=$.source.metrics.http_reqs.values.count"
    )
    assert error.suggestion == "Inspect source and extracted payloads for mapping drift"
