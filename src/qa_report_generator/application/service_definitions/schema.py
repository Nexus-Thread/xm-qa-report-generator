"""Generic Pydantic schema models for extracted k6 metrics."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CounterValues(BaseModel):
    """k6 counter values."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0, description="Use $.metrics.<metric_key>.values.count")
    rate: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.rate")


class RateValues(BaseModel):
    """k6 rate values."""

    model_config = ConfigDict(extra="forbid")

    rate: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.rate")
    passes: int = Field(ge=0, description="Use $.metrics.<metric_key>.values.passes")
    fails: int = Field(ge=0, description="Use $.metrics.<metric_key>.values.fails")


class GaugeValues(BaseModel):
    """k6 gauge values."""

    model_config = ConfigDict(extra="forbid")

    value: float = Field(description="Use $.metrics.<metric_key>.values.value")
    min: float = Field(description="Use $.metrics.<metric_key>.values.min")
    max: float = Field(description="Use $.metrics.<metric_key>.values.max")


class TrendValuesMs(BaseModel):
    """k6 trend values in ms."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    min: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.min")
    avg: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.avg")
    med: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.med")
    max: float = Field(ge=0, description="Use $.metrics.<metric_key>.values.max")
    p95: float = Field(alias="p(95)", ge=0, description='Use $.metrics.<metric_key>.values["p(95)"]')
    p99: float = Field(alias="p(99)", ge=0, description='Use $.metrics.<metric_key>.values["p(99)"]')


class Scenario(BaseModel):
    """Generic extracted k6 scenario settings."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: str = Field(min_length=1, description="Use scenario key under $.execScenarios")
    env_name: str = Field(min_length=1, description="Use $.execScenarios.<scenario>.tags.env_name")
    executor: str = Field(min_length=1, description="Use $.execScenarios.<scenario>.executor")
    rate: float = Field(ge=0, description="Use $.execScenarios.<scenario>.rate")
    duration: str = Field(min_length=1, description="Use $.execScenarios.<scenario>.duration")
    pre_allocated_vus: int = Field(alias="preAllocatedVUs", ge=0, description="Use $.execScenarios.<scenario>.preAllocatedVUs")
    max_vus: int = Field(alias="maxVUs", ge=0, description="Use $.execScenarios.<scenario>.maxVUs")


class ThresholdResult(BaseModel):
    """Threshold evaluation result."""

    model_config = ConfigDict(extra="forbid")

    ok: bool = Field(description='Use $.metrics.<metric_key>.thresholds["<expr>"].ok')


class MetricBase(BaseModel):
    """Shared fields for typed k6 metrics."""

    model_config = ConfigDict(extra="allow")

    type: Literal["counter", "gauge", "rate", "trend"] = Field(description="Use $.metrics.<metric_key>.type")
    contains: Literal["default", "time", "data"] = Field(description="Use $.metrics.<metric_key>.contains")


class CounterMetric(MetricBase):
    """Counter metric wrapper."""

    type: Literal["counter"]
    values: CounterValues = Field(description="Use $.metrics.<metric_key>.values")


class GaugeMetric(MetricBase):
    """Gauge metric wrapper."""

    type: Literal["gauge"]
    values: GaugeValues = Field(description="Use $.metrics.<metric_key>.values")


class RateMetric(MetricBase):
    """Rate metric wrapper."""

    type: Literal["rate"]
    values: RateValues = Field(description="Use $.metrics.<metric_key>.values")
    thresholds: dict[str, ThresholdResult] | None = Field(default=None, description="Use $.metrics.<metric_key>.thresholds")


class TrendMetric(MetricBase):
    """Trend metric wrapper."""

    type: Literal["trend"]
    values: TrendValuesMs = Field(description="Use $.metrics.<metric_key>.values")
    thresholds: dict[str, ThresholdResult] | None = Field(default=None, description="Use $.metrics.<metric_key>.thresholds")


K6Metric = CounterMetric | GaugeMetric | RateMetric | TrendMetric


__all__ = [
    "CounterMetric",
    "CounterValues",
    "GaugeMetric",
    "GaugeValues",
    "K6Metric",
    "MetricBase",
    "RateMetric",
    "RateValues",
    "Scenario",
    "ThresholdResult",
    "TrendMetric",
    "TrendValuesMs",
]
