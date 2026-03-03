"""Megatron extraction output schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .k6_schema import CounterValues, RateValues, TrendValuesMs


class GenericScenario(BaseModel):
    """Scenario-level execution settings."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    env_name: str = Field(min_length=1)
    executor: str = Field(min_length=1)
    rate: float = Field(ge=0)
    duration: str = Field(min_length=1)
    pre_allocated_vus: int = Field(alias="preAllocatedVUs", ge=0)
    max_vus: int = Field(alias="maxVUs", ge=0)


class MegatronExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for megatron service."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: Literal["megatron"]
    report_file: str = Field(min_length=1)
    test_run_duration_ms: float = Field(ge=0)
    scenario: GenericScenario
    checks: RateValues
    http_req_duration: TrendValuesMs
    http_req_failed: RateValues
    http_reqs: CounterValues
    iterations: CounterValues
    dropped_iterations: CounterValues
    thresholds: dict[str, list[str]]


ExtractedMetrics = MegatronExtractedMetrics

REUSED_GENERIC_SCHEMA_TYPES = (CounterValues, RateValues, TrendValuesMs)

__all__ = ["ExtractedMetrics", "GenericScenario", "MegatronExtractedMetrics"]
