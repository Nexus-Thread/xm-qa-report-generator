"""Pydantic schema for megatron k6 extraction output."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MegatronScenario(BaseModel):
    """Scenario-level execution settings."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    env_name: str = Field(min_length=1, description="Use tags.env_name.")
    executor: str = Field(min_length=1)
    rate: float = Field(ge=0)
    duration: str = Field(min_length=1)
    pre_allocated_vus: int = Field(alias="preAllocatedVUs", ge=0)
    max_vus: int = Field(alias="maxVUs", ge=0)


class MegatronChecks(BaseModel):
    """Check rate counters."""

    model_config = ConfigDict(extra="forbid")

    rate: float = Field(ge=0)
    passes: int = Field(ge=0)
    fails: int = Field(ge=0)


class MegatronDurationTrend(BaseModel):
    """Latency trend summary values in milliseconds."""

    model_config = ConfigDict(extra="forbid")

    min: float = Field(ge=0)
    avg: float = Field(ge=0)
    med: float = Field(ge=0)
    max: float = Field(ge=0)
    p95: float = Field(alias="p(95)", ge=0)
    p99: float = Field(alias="p(99)", ge=0)


class MegatronReqFailed(BaseModel):
    """Request failure counters and rate."""

    model_config = ConfigDict(extra="forbid")

    rate: float = Field(ge=0)
    passes: int = Field(ge=0)
    fails: int = Field(ge=0)


class MegatronCounter(BaseModel):
    """Request counter values."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0)
    rate: float = Field(ge=0)


class MegatronExtractedMetrics(BaseModel):
    """Structured deterministic extraction output for megatron service."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    service: str = Field(pattern="^megatron$")
    report_file: str = Field(min_length=1)
    test_run_duration_ms: float = Field(ge=0)
    scenario: MegatronScenario
    checks: MegatronChecks
    http_req_duration: MegatronDurationTrend
    http_req_failed: MegatronReqFailed
    http_reqs: MegatronCounter
    iterations: MegatronCounter
    dropped_iterations: MegatronCounter
    thresholds: dict[str, list[str]]
