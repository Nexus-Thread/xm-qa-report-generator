"""Megatron extraction output schema."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from qa_report_generator.application.service_definitions.schema import CounterValues, RateValues, Scenario, TrendValuesMs


class MegatronExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for megatron service."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["megatron"]
    report_file: str = Field(min_length=1)
    test_run_duration_ms: float = Field(ge=0)
    scenario: Scenario
    checks: RateValues
    http_req_duration: TrendValuesMs
    http_req_failed: RateValues
    http_reqs: CounterValues
    iterations: CounterValues
    dropped_iterations: CounterValues
    thresholds: dict[str, list[str]]


ExtractedMetrics = MegatronExtractedMetrics

__all__ = ["ExtractedMetrics", "MegatronExtractedMetrics"]
