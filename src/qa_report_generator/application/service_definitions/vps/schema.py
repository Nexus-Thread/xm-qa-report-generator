"""Vps extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from qa_report_generator.application.service_definitions import schema as k6_schema


class VpsExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for vps."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["vps"] = k6_schema.service_name_field("vps")
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
    get_vps_eligible_duration: k6_schema.FlexibleTrendMetric = k6_schema.trend_metric_field("K6_Metrics_getVpsEligible_duration")
    get_vps_eligible_counter: k6_schema.FlexibleCounterMetric = k6_schema.counter_metric_field("K6_Metrics_getVpsEligible_counter")
    get_vps_eligible_fail_counter: k6_schema.FlexibleCounterMetric = k6_schema.counter_metric_field("K6_Metrics_getVpsEligible_failCounter")
    thresholds: dict[str, list[str]] = k6_schema.thresholds_field()


ExtractedMetrics = VpsExtractedMetrics

VpsExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "CounterValues": k6_schema.CounterValues,
        "FlexibleCounterMetric": k6_schema.FlexibleCounterMetric,
        "FlexibleTrendMetric": k6_schema.FlexibleTrendMetric,
    }
)

__all__ = ["ExtractedMetrics", "VpsExtractedMetrics"]
