"""Unit tests for schema-driven merge strategy helpers."""

from __future__ import annotations

from qa_report_generator_performance.application.service_definitions.services.symbolstreeservice.schema import (
    SymbolstreeserviceExtractedMetrics,
)
from qa_report_generator_performance.application.service_definitions.shared import derive_merge_buckets


def test_derive_merge_buckets_from_symbolstreeservice_schema() -> None:
    """Merge buckets are derived from schema field types rather than hard-coded lists."""
    result = derive_merge_buckets(SymbolstreeserviceExtractedMetrics)

    assert result.trend_fields == (
        "http_req_duration",
        "http_req_blocked",
        "http_req_connecting",
        "http_req_receiving",
        "http_req_sending",
        "http_req_tls_handshaking",
        "http_req_waiting",
        "iteration_duration",
    )
    assert result.rate_fields == (
        "http_req_failed",
        "checks",
    )
    assert result.counter_fields == (
        "http_reqs",
        "iterations",
        "data_received",
        "data_sent",
    )
    assert result.optional_counter_fields == ("dropped_iterations",)
