"""Shared helpers for schema-driven metric merge strategies."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Any, get_args

from pydantic import BaseModel

from . import schema as shared_schema

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class SchemaMergeBuckets:
    """Schema-derived buckets describing how extracted fields should merge."""

    trend_fields: tuple[str, ...]
    rate_fields: tuple[str, ...]
    counter_fields: tuple[str, ...]
    optional_counter_fields: tuple[str, ...]


@cache
def derive_merge_buckets(schema_model: type[BaseModel]) -> SchemaMergeBuckets:
    """Derive merge buckets from a service extraction schema model."""
    trend_fields: list[str] = []
    rate_fields: list[str] = []
    counter_fields: list[str] = []
    optional_counter_fields: list[str] = []

    for field_name, field_info in schema_model.model_fields.items():
        annotation = field_info.annotation
        if annotation is shared_schema.TrendValuesMs:
            trend_fields.append(field_name)
            continue
        if annotation is shared_schema.RateValues:
            rate_fields.append(field_name)
            continue
        if annotation is shared_schema.CounterValues:
            counter_fields.append(field_name)
            continue
        if _is_optional_annotation(annotation, target_type=shared_schema.CounterValues):
            optional_counter_fields.append(field_name)

    return SchemaMergeBuckets(
        trend_fields=tuple(trend_fields),
        rate_fields=tuple(rate_fields),
        counter_fields=tuple(counter_fields),
        optional_counter_fields=tuple(optional_counter_fields),
    )


def merge_trend_metric_field(
    *,
    extracted_runs: Sequence[BaseModel],
    field_name: str,
    weight_field_name: str = "iterations",
) -> dict[str, float]:
    """Merge one trend metric field using weighted averages and guardrail percentiles."""
    weights = [_required_int(_required_model(getattr(run, weight_field_name), weight_field_name), "count") for run in extracted_runs]
    total_weight = sum(weights)
    values = [_required_model(getattr(run, field_name), field_name) for run in extracted_runs]
    return {
        "min": min(_required_float(value, "min") for value in values),
        "avg": _weighted_average(
            values=[_required_float(value, "avg") for value in values],
            weights=weights,
            fallback_divisor=total_weight,
        ),
        "med": _weighted_average(
            values=[_required_float(value, "med") for value in values],
            weights=weights,
            fallback_divisor=total_weight,
        ),
        "max": max(_required_float(value, "max") for value in values),
        "p(95)": max(_required_float_by_alias(value, field_name="p95", alias="p(95)") for value in values),
        "p(99)": max(_required_float_by_alias(value, field_name="p99", alias="p(99)") for value in values),
    }


def merge_rate_metric_field(
    *,
    extracted_runs: Sequence[BaseModel],
    field_name: str,
) -> dict[str, float | int]:
    """Merge one rate metric field from summed pass/fail counts."""
    values = [_required_model(getattr(run, field_name), field_name) for run in extracted_runs]
    passes = sum(_required_int(value, "passes") for value in values)
    fails = sum(_required_int(value, "fails") for value in values)
    total = passes + fails
    return {
        "rate": fails / total if total else 0.0,
        "passes": passes,
        "fails": fails,
    }


def merge_counter_metric_field(
    *,
    extracted_runs: Sequence[BaseModel],
    field_name: str,
) -> dict[str, float | int]:
    """Merge one counter metric field by summing counts and rates."""
    values = [_required_model(getattr(run, field_name), field_name) for run in extracted_runs]
    return {
        "count": sum(_required_int(value, "count") for value in values),
        "rate": sum(_required_float(value, "rate") for value in values),
    }


def merge_optional_counter_metric_field(
    *,
    extracted_runs: Sequence[BaseModel],
    field_name: str,
) -> dict[str, float | int] | None:
    """Merge one optional counter metric field when present in any source run."""
    values = [getattr(run, field_name) for run in extracted_runs]
    present_values = [value for value in values if isinstance(value, BaseModel)]
    if not present_values:
        return None
    return {
        "count": sum(_required_int(value, "count") for value in present_values),
        "rate": sum(_required_float(value, "rate") for value in present_values),
    }


def _is_optional_annotation(annotation: Any, *, target_type: type[BaseModel]) -> bool:
    """Return whether an annotation is exactly Optional[target_type]."""
    annotation_args = get_args(annotation)
    if not annotation_args or type(None) not in annotation_args:
        return False
    non_none_args = tuple(arg for arg in annotation_args if arg is not type(None))
    return len(non_none_args) == 1 and non_none_args[0] is target_type


def _required_model(value: Any, field_name: str) -> BaseModel:
    """Return one required nested model field."""
    if isinstance(value, BaseModel):
        return value
    msg = f"Prepared extracted model is missing nested model field: {field_name}"
    raise TypeError(msg)


def _required_int(payload: BaseModel, field_name: str) -> int:
    """Return one required integer field from a nested model."""
    value = getattr(payload, field_name, None)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    msg = f"Prepared extracted model is missing integer field: {field_name}"
    raise TypeError(msg)


def _required_float(payload: BaseModel, field_name: str) -> float:
    """Return one required numeric field from a nested model."""
    value = getattr(payload, field_name, None)
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    msg = f"Prepared extracted model is missing numeric field: {field_name}"
    raise TypeError(msg)


def _required_float_by_alias(payload: BaseModel, *, field_name: str, alias: str) -> float:
    """Return one required numeric field from a nested model with alias-aware errors."""
    value = getattr(payload, field_name, None)
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    msg = f"Prepared extracted model is missing numeric field: {alias}"
    raise TypeError(msg)


def _weighted_average(*, values: list[float], weights: list[int], fallback_divisor: int) -> float:
    """Calculate a weighted average with a deterministic zero fallback."""
    weighted_sum = sum(value * weight for value, weight in zip(values, weights, strict=True))
    if fallback_divisor <= 0:
        return 0.0
    return weighted_sum / fallback_divisor
