"""Symbolsservice extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from qa_report_generator.application.service_definitions import schema as k6_schema


class SymbolsserviceExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for symbolsservice."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["symbolsservice"] = k6_schema.service_name_field("symbolsservice")
    report_file: str = k6_schema.report_file_field()
    test_run_duration_ms: float = k6_schema.test_run_duration_ms_field()
    scenario: k6_schema.Scenario = k6_schema.scenario_field()
    checks: k6_schema.RateValues = k6_schema.metric_values_field("checks")
    http_req_failed: k6_schema.RateValues = k6_schema.metric_values_field("http_req_failed{test_name:<scenario>}")
    http_reqs: k6_schema.CounterValues = k6_schema.metric_values_field("http_reqs")
    iterations: k6_schema.CounterValues = k6_schema.metric_values_field("iterations")
    post_visible_symbols_state_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field(
        "K6_Metrics_postVisibleSymbolsState_duration"
    )
    post_visible_symbols_state_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_postVisibleSymbolsState_counter"
    )
    post_visible_symbols_filter_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field(
        "K6_Metrics_postVisibleSymbolsFilter_duration"
    )
    post_visible_symbols_filter_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_postVisibleSymbolsFilter_counter"
    )
    post_symbols_state_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_postSymbolsState_duration")
    post_symbols_state_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_postSymbolsState_counter")
    post_last_tick_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_postLastTick_duration")
    post_last_tick_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_postLastTick_counter")
    thresholds: dict[str, list[str]] = k6_schema.thresholds_field()


ExtractedMetrics = SymbolsserviceExtractedMetrics

SymbolsserviceExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "CounterValues": k6_schema.CounterValues,
        "FlexibleCounterMetric": k6_schema.FlexibleCounterMetric,
        "FlexibleTrendMetric": k6_schema.FlexibleTrendMetric,
    }
)

__all__ = ["ExtractedMetrics", "SymbolsserviceExtractedMetrics"]
