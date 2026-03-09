"""Symbolstreeservice extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from qa_report_generator.application.service_definitions import schema as k6_schema


class SymbolstreeserviceExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for symbolstreeservice."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["symbolstreeservice"] = k6_schema.service_name_field("symbolstreeservice")
    report_file: str = k6_schema.report_file_field()
    test_run_duration_ms: float = k6_schema.test_run_duration_ms_field()
    scenario: k6_schema.Scenario = k6_schema.scenario_field()
    checks: k6_schema.RateValues = k6_schema.metric_values_field("checks")
    http_req_failed: k6_schema.RateValues = k6_schema.metric_values_field("http_req_failed{test_name:<scenario>}")
    http_reqs: k6_schema.CounterValues = k6_schema.metric_values_field("http_reqs")
    iterations: k6_schema.CounterValues = k6_schema.metric_values_field("iterations")
    get_symbols_tree_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTree_duration")
    get_symbols_tree_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTree_counter")
    get_symbols_tree_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTree_failCounter")
    get_symbols_tree_info0_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTreeInfo0_duration")
    get_symbols_tree_info0_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTreeInfo0_counter")
    get_symbols_tree_info0_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_getSymbolsTreeInfo0_failCounter"
    )
    get_symbols_tree_info1_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTreeInfo1_duration")
    get_symbols_tree_info1_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTreeInfo1_counter")
    get_symbols_tree_info1_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_getSymbolsTreeInfo1_failCounter"
    )
    get_symbols_tree_info2_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTreeInfo2_duration")
    get_symbols_tree_info2_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTreeInfo2_counter")
    get_symbols_tree_info2_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_getSymbolsTreeInfo2_failCounter"
    )
    get_symbols_tree_info3_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTreeInfo3_duration")
    get_symbols_tree_info3_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTreeInfo3_counter")
    get_symbols_tree_info3_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_getSymbolsTreeInfo3_failCounter"
    )
    get_symbols_tree_info4_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTreeInfo4_duration")
    get_symbols_tree_info4_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTreeInfo4_counter")
    get_symbols_tree_info4_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_getSymbolsTreeInfo4_failCounter"
    )
    get_symbols_tree_info5_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTreeInfo5_duration")
    get_symbols_tree_info5_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTreeInfo5_counter")
    get_symbols_tree_info5_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_getSymbolsTreeInfo5_failCounter"
    )
    get_symbols_tree_info6_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTreeInfo6_duration")
    get_symbols_tree_info6_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTreeInfo6_counter")
    get_symbols_tree_info6_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_getSymbolsTreeInfo6_failCounter"
    )
    get_symbols_tree_info7_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_getSymbolsTreeInfo7_duration")
    get_symbols_tree_info7_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_getSymbolsTreeInfo7_counter")
    get_symbols_tree_info7_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_getSymbolsTreeInfo7_failCounter"
    )
    thresholds: dict[str, list[str]] = k6_schema.thresholds_field()


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
