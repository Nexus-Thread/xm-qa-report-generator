"""Megatron extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from qa_report_generator.application.service_definitions import schema as k6_schema


class MegatronExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for megatron service."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["megatron"]
    report_file: str = Field(min_length=1)
    test_run_duration_ms: float = Field(ge=0)
    scenario: k6_schema.Scenario
    checks: k6_schema.RateValues
    http_req_duration: k6_schema.TrendValuesMs
    http_req_failed: k6_schema.RateValues
    http_reqs: k6_schema.CounterValues
    iterations: k6_schema.CounterValues
    dropped_iterations: k6_schema.CounterValues
    thresholds: dict[str, list[str]]

    @model_validator(mode="after")
    def validate_scenario_bounds(self) -> MegatronExtractedMetrics:
        """Ensure scenario VU bounds are valid."""
        if self.scenario.max_vus < self.scenario.pre_allocated_vus:
            msg = "maxVUs must be >= preAllocatedVUs"
            raise ValueError(msg)
        return self


ExtractedMetrics = MegatronExtractedMetrics

MegatronExtractedMetrics.model_rebuild(
    _types_namespace={
        "Scenario": k6_schema.Scenario,
        "RateValues": k6_schema.RateValues,
        "TrendValuesMs": k6_schema.TrendValuesMs,
        "CounterValues": k6_schema.CounterValues,
    }
)

__all__ = ["ExtractedMetrics", "MegatronExtractedMetrics"]
