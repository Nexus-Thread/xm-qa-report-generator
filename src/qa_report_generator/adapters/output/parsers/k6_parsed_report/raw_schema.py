"""Internal schema for validating raw k6 summary payloads in parser adapter."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class K6RawState(BaseModel):
    """k6 runtime state fields used by parser mapping."""

    model_config = ConfigDict(extra="allow")

    test_run_duration_ms: float = Field(alias="testRunDurationMs", ge=0)


class K6RawExecScenario(BaseModel):
    """Scenario definition under the `execScenarios` report object."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    executor: str = Field(min_length=1)
    rate: float | None = Field(default=None, ge=0)
    duration: str | None = Field(default=None, min_length=1)
    pre_allocated_vus: int | None = Field(default=None, alias="preAllocatedVUs", ge=0)
    max_vus: int | None = Field(default=None, alias="maxVUs", ge=0)
    tags: dict[str, Any] | None = Field(default=None)


class K6RawSummary(BaseModel):
    """Raw k6 summary input shape validated before domain mapping."""

    model_config = ConfigDict(extra="allow")

    state: K6RawState | None = Field(default=None)
    exec_scenarios: dict[str, K6RawExecScenario] = Field(alias="execScenarios", default_factory=dict)
    exec_thresholds: dict[str, list[str]] = Field(alias="execThresholds", default_factory=dict)
