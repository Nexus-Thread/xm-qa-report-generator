"""Generic Pydantic schema models for extracted k6 metrics."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def service_name_field(service_name: str) -> Any:
    """Build a service-name field with reusable extraction guidance."""
    return Field(description=f"Use literal service name '{service_name}'")


def report_file_field() -> Any:
    """Build a report-file field with reusable extraction guidance."""
    return Field(
        min_length=1,
        description="Use verification_context.report_file, populated from the selected scenario source report filename",
    )


def test_run_duration_ms_field() -> Any:
    """Build a runtime field with reusable extraction guidance."""
    return Field(ge=0, description="Use $.state.testRunDurationMs")


def scenario_field() -> Any:
    """Build a scenario field with reusable extraction guidance."""
    return Field(description="Use the selected scenario from $.execScenarios")


def metric_values_field(
    metric_key: str,
    *,
    prefer_scenario_tagged: bool = False,
    optional: bool = False,
) -> Any:
    """Build a metric field with reusable extraction guidance."""
    description = f"Use $.metrics.{metric_key}.values"
    if prefer_scenario_tagged:
        description = f"Use scenario-tagged $.metrics.{metric_key}{{test_name:<scenario>}}.values when present, otherwise use $.metrics.{metric_key}.values"
    if optional:
        description = f"{description} when present; otherwise use null"
    return Field(description=description)


def thresholds_field() -> Any:
    """Build a thresholds field with reusable extraction guidance."""
    return Field(description="Use $.execThresholds")


def counter_metric_field(metric_key: str) -> Any:
    """Build a typed counter metric field for a full custom metric."""
    return Field(description=f"Use $.metrics.{metric_key}")


def trend_metric_field(metric_key: str) -> Any:
    """Build a typed trend metric field for a full custom metric."""
    return Field(description=f"Use $.metrics.{metric_key}")


def optional_counter_metric_field(metric_key: str) -> Any:
    """Build an optional typed counter metric field for a full custom metric."""
    return Field(default=None, description=f"Use $.metrics.{metric_key} when present; otherwise use null")


def optional_trend_metric_field(metric_key: str) -> Any:
    """Build an optional typed trend metric field for a full custom metric."""
    return Field(default=None, description=f"Use $.metrics.{metric_key} when present; otherwise use null")


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

    @model_validator(mode="after")
    def validate_vu_bounds(self) -> Scenario:
        """Validate that max VUs is not lower than preallocated VUs."""
        if self.max_vus < self.pre_allocated_vus:
            msg = "maxVUs must be >= preAllocatedVUs"
            raise ValueError(msg)
        return self


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


class FlexibleCounterMetric(BaseModel):
    """Typed full counter metric with flexible contains value."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["counter"] = Field(description="Use $.metrics.<metric_key>.type")
    contains: str = Field(description="Use $.metrics.<metric_key>.contains")
    values: CounterValues = Field(description="Use $.metrics.<metric_key>.values")


class FlexibleTrendMetric(BaseModel):
    """Typed full trend metric with flexible contains value."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["trend"] = Field(description="Use $.metrics.<metric_key>.type")
    contains: str = Field(description="Use $.metrics.<metric_key>.contains")
    values: TrendValuesMs = Field(description="Use $.metrics.<metric_key>.values")
    thresholds: dict[str, ThresholdResult] | None = Field(
        default=None,
        description="Use $.metrics.<metric_key>.thresholds",
    )


K6Metric = CounterMetric | GaugeMetric | RateMetric | TrendMetric


__all__ = [
    "CounterMetric",
    "CounterValues",
    "FlexibleCounterMetric",
    "FlexibleTrendMetric",
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
    "counter_metric_field",
    "metric_values_field",
    "optional_counter_metric_field",
    "optional_trend_metric_field",
    "report_file_field",
    "scenario_field",
    "service_name_field",
    "test_run_duration_ms_field",
    "thresholds_field",
    "trend_metric_field",
]
