"""Symbolstreeservice extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from qa_report_generator.application.service_definitions.shared import schema as k6_schema


class SymbolstreeserviceExtractedMetrics(k6_schema.K6HttpExtractedMetrics):
    """Structured deterministic extraction output for symbolstreeservice."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["symbolstreeservice"] = k6_schema.service_name_field("symbolstreeservice")
    report_file: str = k6_schema.report_file_field()
    source_scenarios: list[str] | None = Field(
        default=None,
        description="Internal grouped scenario provenance",
        json_schema_extra={"internal": True},
    )
    group_size: int | None = Field(
        default=None,
        ge=1,
        description="Internal grouped scenario count",
        json_schema_extra={"internal": True},
    )


ExtractedMetrics = SymbolstreeserviceExtractedMetrics

SymbolstreeserviceExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "CounterValues": k6_schema.CounterValues,
        "FlexibleCounterMetric": k6_schema.FlexibleCounterMetric,
        "FlexibleTrendMetric": k6_schema.FlexibleTrendMetric,
    }
)

__all__ = ["ExtractedMetrics", "SymbolstreeserviceExtractedMetrics"]
