"""Vps extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict

from qa_report_generator.application.service_definitions.shared import schema as k6_schema


class VpsExtractedMetrics(k6_schema.K6HttpExtractedMetrics):
    """Structured deterministic extraction output for vps."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["vps"] = k6_schema.service_name_field("vps")
    report_file: str = k6_schema.report_file_field()


ExtractedMetrics = VpsExtractedMetrics

VpsExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "TrendValuesMs": k6_schema.TrendValuesMs,
        "CounterValues": k6_schema.CounterValues,
        "FlexibleCounterMetric": k6_schema.FlexibleCounterMetric,
        "FlexibleTrendMetric": k6_schema.FlexibleTrendMetric,
    }
)

__all__ = ["ExtractedMetrics", "VpsExtractedMetrics"]
