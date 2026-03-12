"""Tradinghistoricaldata extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict

from qa_report_generator.application.service_definitions.shared import schema as k6_schema


class TradinghistoricaldataExtractedMetrics(k6_schema.K6HttpExtractedMetrics):
    """Structured deterministic extraction output for tradinghistoricaldata."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["tradinghistoricaldata"] = k6_schema.service_name_field("tradinghistoricaldata")
    report_file: str = k6_schema.report_file_field()


ExtractedMetrics = TradinghistoricaldataExtractedMetrics

TradinghistoricaldataExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "CounterValues": k6_schema.CounterValues,
        "FlexibleCounterMetric": k6_schema.FlexibleCounterMetric,
        "FlexibleTrendMetric": k6_schema.FlexibleTrendMetric,
    }
)

__all__ = ["ExtractedMetrics", "TradinghistoricaldataExtractedMetrics"]
