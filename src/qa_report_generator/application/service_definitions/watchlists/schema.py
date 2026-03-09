"""Watchlists extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from qa_report_generator.application.service_definitions import schema as k6_schema


class WatchlistsExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for watchlists."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["watchlists"] = k6_schema.service_name_field("watchlists")
    report_file: str = k6_schema.report_file_field()
    test_run_duration_ms: float = k6_schema.test_run_duration_ms_field()
    scenario: k6_schema.Scenario = k6_schema.scenario_field()
    checks: k6_schema.RateValues = k6_schema.metric_values_field("checks")
    http_req_failed: k6_schema.RateValues = k6_schema.metric_values_field("http_req_failed{test_name:<scenario>}")
    http_reqs: k6_schema.CounterValues = k6_schema.metric_values_field("http_reqs")
    iterations: k6_schema.CounterValues = k6_schema.metric_values_field("iterations")
    get_v4_watchlists1_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getV4Watchlists1_duration")
    get_v4_watchlists1_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getV4Watchlists1_counter")
    get_v4_watchlists0_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getV4Watchlists0_duration")
    get_v4_watchlists0_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getV4Watchlists0_counter")
    get_v1_watchlists_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getV1Watchlists_duration")
    get_v1_watchlists_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getV1Watchlists_counter")
    thresholds: dict[str, list[str]] = k6_schema.thresholds_field()


ExtractedMetrics = WatchlistsExtractedMetrics

WatchlistsExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "CounterValues": k6_schema.CounterValues,
        "FlexibleCounterMetric": k6_schema.FlexibleCounterMetric,
        "FlexibleTrendMetric": k6_schema.FlexibleTrendMetric,
    }
)

__all__ = ["ExtractedMetrics", "WatchlistsExtractedMetrics"]
