"""Trading extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from qa_report_generator.application.service_definitions import schema as k6_schema


def counter_metric_field(metric_key: str) -> CounterMetric:
    """Build a typed counter metric field for a custom k6 metric."""
    return Field(description=f"Use $.metrics.{metric_key}")


def trend_metric_field(metric_key: str) -> TrendMetric:
    """Build a typed trend metric field for a custom k6 metric."""
    return Field(description=f"Use $.metrics.{metric_key}")


class CounterMetric(BaseModel):
    """Typed custom counter metric."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["counter"] = Field(description="Use $.metrics.<metric_key>.type")
    contains: str = Field(description="Use $.metrics.<metric_key>.contains")
    values: k6_schema.CounterValues = Field(description="Use $.metrics.<metric_key>.values")


class TrendMetric(BaseModel):
    """Typed custom trend metric."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["trend"] = Field(description="Use $.metrics.<metric_key>.type")
    contains: str = Field(description="Use $.metrics.<metric_key>.contains")
    values: k6_schema.TrendValuesMs = Field(description="Use $.metrics.<metric_key>.values")
    thresholds: dict[str, k6_schema.ThresholdResult] | None = Field(
        default=None,
        description="Use $.metrics.<metric_key>.thresholds",
    )


class TradingExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for trading service."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["trading"] = k6_schema.service_name_field("trading")
    report_file: str = k6_schema.report_file_field()
    test_run_duration_ms: float = k6_schema.test_run_duration_ms_field()
    scenario: k6_schema.Scenario = k6_schema.scenario_field()
    checks: k6_schema.RateValues = k6_schema.metric_values_field("checks")
    http_req_failed: k6_schema.RateValues = k6_schema.metric_values_field("http_req_failed{test_name:<scenario>}")
    http_reqs: k6_schema.CounterValues = k6_schema.metric_values_field("http_reqs")
    iterations: k6_schema.CounterValues = k6_schema.metric_values_field("iterations")
    get_open_and_close_order_duration: TrendMetric = trend_metric_field("K6_Metrics_getOpenAndCloseOrder_duration")
    get_open_and_close_order_counter: CounterMetric = counter_metric_field("K6_Metrics_getOpenAndCloseOrder_counter")
    post_open_order_duration: TrendMetric = trend_metric_field("K6_Metrics_post_open_order_duration")
    post_open_order_counter: CounterMetric = counter_metric_field("K6_Metrics_post_open_order_counter")
    post_close_trade_duration: TrendMetric = trend_metric_field("K6_Metrics_post_close_trade_duration")
    post_close_trade_counter: CounterMetric = counter_metric_field("K6_Metrics_post_close_trade_counter")
    deposit_balance_duration: TrendMetric = trend_metric_field("K6_Metrics_depositBalance_duration")
    deposit_balance_counter: CounterMetric = counter_metric_field("K6_Metrics_depositBalance_counter")
    login_email_duration: TrendMetric = trend_metric_field("K6_Metrics_login_email_duration")
    login_email_fail_counter: CounterMetric = counter_metric_field("K6_Metrics_login_email_failCounter")
    thresholds: dict[str, list[str]] = k6_schema.thresholds_field()


ExtractedMetrics = TradingExtractedMetrics

TradingExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "TrendValuesMs": k6_schema.TrendValuesMs,
        "CounterValues": k6_schema.CounterValues,
        "ThresholdResult": k6_schema.ThresholdResult,
    }
)

__all__ = [
    "CounterMetric",
    "ExtractedMetrics",
    "TradingExtractedMetrics",
    "TrendMetric",
]
