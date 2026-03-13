"""Trading extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict

from qa_report_generator_performance.application.service_definitions.shared import schema as k6_schema


class TradingExtractedMetrics(k6_schema.K6HttpExtractedMetrics):
    """Structured deterministic extraction output for trading service."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["trading"] = k6_schema.service_name_field("trading")
    report_file: str = k6_schema.report_file_field()

    scenario: k6_schema.Scenario = k6_schema.scenario_field()
    thresholds: dict[str, list[str]] = k6_schema.thresholds_field()
    threshold_statuses: dict[str, dict[str, bool]] = k6_schema.threshold_statuses_field()

    http_req_duration: k6_schema.TrendValuesMs = k6_schema.metric_values_field("http_req_duration", prefer_scenario_tagged=True)
    http_req_blocked: k6_schema.TrendValuesMs = k6_schema.metric_values_field("http_req_blocked")
    http_req_connecting: k6_schema.TrendValuesMs = k6_schema.metric_values_field("http_req_connecting")
    http_req_receiving: k6_schema.TrendValuesMs = k6_schema.metric_values_field("http_req_receiving")
    http_req_sending: k6_schema.TrendValuesMs = k6_schema.metric_values_field("http_req_sending")
    http_req_tls_handshaking: k6_schema.TrendValuesMs = k6_schema.metric_values_field("http_req_tls_handshaking")
    http_req_waiting: k6_schema.TrendValuesMs = k6_schema.metric_values_field("http_req_waiting")
    iteration_duration: k6_schema.TrendValuesMs = k6_schema.metric_values_field("iteration_duration")

    http_req_failed: k6_schema.RateValues = k6_schema.metric_values_field("http_req_failed", prefer_scenario_tagged=True)
    checks: k6_schema.RateValues = k6_schema.metric_values_field("checks")

    http_reqs: k6_schema.CounterValues = k6_schema.metric_values_field("http_reqs")
    iterations: k6_schema.CounterValues = k6_schema.metric_values_field("iterations")
    data_received: k6_schema.CounterValues = k6_schema.metric_values_field("data_received")
    data_sent: k6_schema.CounterValues = k6_schema.metric_values_field("data_sent")
    dropped_iterations: k6_schema.CounterValues | None = k6_schema.metric_values_field("dropped_iterations", optional=True)


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
