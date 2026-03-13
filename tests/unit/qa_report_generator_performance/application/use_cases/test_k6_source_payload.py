"""Unit tests for raw k6 source-payload helpers."""

from __future__ import annotations

from qa_report_generator_performance.application.use_cases.k6_service_extraction.thresholds import (
    build_threshold_summaries_from_source_payload,
)


def test_build_threshold_summaries_from_source_payload_preserves_pass_fail() -> None:
    """Threshold summary builder maps raw k6 threshold results to statuses."""
    source_payload = {
        "metrics": {
            "http_req_duration": {
                "thresholds": {
                    "p(95)<1000": {"ok": True},
                    "p(99)<1500": {"ok": False},
                }
            }
        },
        "thresholds": {"http_req_duration": ["p(95)<1000", "p(99)<1500"]},
    }

    result = build_threshold_summaries_from_source_payload(source_payload=source_payload)

    assert [(item.metric_key, item.expression, item.status) for item in result] == [
        ("http_req_duration", "p(95)<1000", "pass"),
        ("http_req_duration", "p(99)<1500", "fail"),
    ]
