"""Tradinghistoricaldata extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from qa_report_generator.application.service_definitions import schema as k6_schema


class TradinghistoricaldataExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for tradinghistoricaldata."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["tradinghistoricaldata"] = k6_schema.service_name_field("tradinghistoricaldata")
    report_file: str = k6_schema.report_file_field()
    test_run_duration_ms: float = k6_schema.test_run_duration_ms_field()
    scenario: k6_schema.Scenario = k6_schema.scenario_field()
    checks: k6_schema.RateValues = k6_schema.metric_values_field("checks")
    http_req_failed: k6_schema.RateValues = k6_schema.metric_values_field("http_req_failed{test_name:<scenario>}")
    http_reqs: k6_schema.CounterValues = k6_schema.metric_values_field("http_reqs")
    iterations: k6_schema.CounterValues = k6_schema.metric_values_field("iterations")
    dropped_iterations: k6_schema.CounterValues | None = k6_schema.metric_values_field(
        "dropped_iterations",
        optional=True,
    )
    login_email_duration: k6_schema.FlexibleTrendMetric = k6_schema.trend_metric_field("K6_Metrics_login_email_duration")
    login_email_counter: k6_schema.FlexibleCounterMetric = k6_schema.counter_metric_field("K6_Metrics_login_email_counter")
    thd_candles_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_thd_candles_duration")
    thd_candles_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_thd_candles_counter")
    thd_candles_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_thd_candles_failCounter")
    thd_trading_history_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_thd_trading_history_duration")
    thd_trading_history_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_thd_trading_history_counter")
    thd_trading_history_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field(
        "K6_Metrics_thd_trading_history_failCounter"
    )
    thd_orders_duration: k6_schema.FlexibleTrendMetric | None = k6_schema.optional_trend_metric_field("K6_Metrics_thd_orders_duration")
    thd_orders_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_thd_orders_counter")
    thd_orders_fail_counter: k6_schema.FlexibleCounterMetric | None = k6_schema.optional_counter_metric_field("K6_Metrics_thd_orders_failCounter")
    thresholds: dict[str, list[str]] = k6_schema.thresholds_field()


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
