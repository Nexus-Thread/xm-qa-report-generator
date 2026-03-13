"""Application helpers for building threshold summaries from raw k6 payloads."""

from __future__ import annotations

from typing import Any

from qa_report_generator_performance.domain.analytics import K6ThresholdSummary

from .source_payload import (
    collect_threshold_statuses,
    normalize_threshold_definitions_from_source_payload,
)


def build_threshold_summaries_from_source_payload(*, source_payload: dict[str, Any]) -> list[K6ThresholdSummary]:
    """Build threshold summaries directly from a raw k6 source payload."""
    threshold_definitions = normalize_threshold_definitions_from_source_payload(source_payload=source_payload)
    threshold_statuses = collect_threshold_statuses(metric_payloads=_as_dict(source_payload.get("metrics")))

    summaries: list[K6ThresholdSummary] = []
    for metric_key, expressions in sorted(threshold_definitions.items()):
        summaries.extend(
            K6ThresholdSummary(
                metric_key=metric_key,
                expression=expression,
                status=threshold_statuses.get((metric_key, expression), "unknown"),
            )
            for expression in expressions
        )

    return summaries


def _as_dict(value: Any) -> dict[str, Any]:
    """Return a dict value or an empty dict fallback."""
    return value if isinstance(value, dict) else {}
