"""Trading extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict

from qa_report_generator.application.service_definitions import schema as k6_schema


class TradingExtractedMetrics(k6_schema.K6HttpExtractedMetrics):
    """Structured deterministic extraction output for trading service."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["trading"] = k6_schema.service_name_field("trading")
    report_file: str = k6_schema.report_file_field()


ExtractedMetrics = TradingExtractedMetrics

TradingExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "TrendValuesMs": k6_schema.TrendValuesMs,
        "CounterValues": k6_schema.CounterValues,
        "ThresholdResult": k6_schema.ThresholdResult,
        "FlexibleCounterMetric": k6_schema.FlexibleCounterMetric,
        "FlexibleTrendMetric": k6_schema.FlexibleTrendMetric,
    }
)

__all__ = ["ExtractedMetrics", "TradingExtractedMetrics"]
