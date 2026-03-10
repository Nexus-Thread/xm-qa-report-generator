"""Post-processing for derived symbolstreeservice outputs."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING, cast

from qa_report_generator.application.dtos import K6ServiceExtractionRun

if TYPE_CHECKING:
    from pydantic import BaseModel

    from .schema import SymbolstreeserviceExtractedMetrics

_GROUPED_SCENARIO_PATTERN = re.compile(r"^(?P<base>getSymbolsTreeInfo)\d+$")
_GROUPED_SCENARIO_NAME_FRAGMENT_PATTERN = re.compile(r"getSymbolsTreeInfo\d+")
_TREND_METRIC_FIELDS = (
    "http_req_duration",
    "http_req_blocked",
    "http_req_connecting",
    "http_req_receiving",
    "http_req_sending",
    "http_req_tls_handshaking",
    "http_req_waiting",
    "iteration_duration",
)
_RATE_METRIC_FIELDS = ("checks", "http_req_failed")
_COUNTER_METRIC_FIELDS = (
    "http_reqs",
    "iterations",
    "data_received",
    "data_sent",
)


def build_post_processed_runs(
    extracted_runs: list[BaseModel],
) -> list[K6ServiceExtractionRun]:
    """Build grouped derived runs for numbered getSymbolsTreeInfo scenarios."""
    symbol_tree_runs = [_to_symbolstreeservice_metrics(run) for run in extracted_runs]
    passthrough_runs: list[K6ServiceExtractionRun] = []
    grouped_runs: dict[str, list[SymbolstreeserviceExtractedMetrics]] = defaultdict(list)

    for extracted_run in symbol_tree_runs:
        match = _GROUPED_SCENARIO_PATTERN.match(extracted_run.scenario.name)
        if match is None:
            passthrough_runs.append(
                K6ServiceExtractionRun(
                    source_report_files=[extracted_run.report_file],
                    extracted=_to_final_run_payload(extracted_run.model_dump(by_alias=True)),
                )
            )
            continue
        grouped_runs[match.group("base")].append(extracted_run)

    merged_runs = [_build_grouped_run(name=group_name, extracted_runs=group_runs) for group_name, group_runs in sorted(grouped_runs.items())]
    return sorted(
        [*passthrough_runs, *merged_runs],
        key=lambda run: str(run.extracted.get("scenario", {}).get("name", "")),
    )


def _build_grouped_run(
    *,
    name: str,
    extracted_runs: list[SymbolstreeserviceExtractedMetrics],
) -> K6ServiceExtractionRun:
    """Build one grouped derived run from multiple extracted runs."""
    representative_run = extracted_runs[0]
    source_report_files = sorted(run.report_file for run in extracted_runs)
    total_iterations = sum(run.iterations.count for run in extracted_runs)
    duration_values = {run.test_run_duration_ms for run in extracted_runs}

    grouped_payload = representative_run.model_dump(by_alias=True)
    grouped_payload["scenario"] = {
        **grouped_payload["scenario"],
        "name": name,
        "rate": sum(run.scenario.rate for run in extracted_runs),
        "preAllocatedVUs": max(run.scenario.pre_allocated_vus for run in extracted_runs),
        "maxVUs": max(run.scenario.max_vus for run in extracted_runs),
    }
    grouped_payload["test_run_duration_ms"] = duration_values.pop() if len(duration_values) == 1 else max(run.test_run_duration_ms for run in extracted_runs)
    grouped_payload["thresholds"] = _merge_thresholds(name=name, extracted_runs=extracted_runs)
    for field_name in _TREND_METRIC_FIELDS:
        grouped_payload[field_name] = _merge_trend_metric_values(
            extracted_runs=extracted_runs,
            field_name=field_name,
            total_iterations=total_iterations,
        )
    for field_name in _RATE_METRIC_FIELDS:
        grouped_payload[field_name] = _merge_rate_metric_values(
            extracted_runs=extracted_runs,
            field_name=field_name,
        )
    for field_name in _COUNTER_METRIC_FIELDS:
        grouped_payload[field_name] = _merge_counter_metric_values(
            extracted_runs=extracted_runs,
            field_name=field_name,
        )
    grouped_payload["dropped_iterations"] = _merge_optional_counter_metric_values(
        extracted_runs=extracted_runs,
        field_name="dropped_iterations",
    )
    grouped_payload["source_scenarios"] = [run.scenario.name for run in extracted_runs]
    grouped_payload["group_size"] = len(extracted_runs)
    grouped_payload["source_report_files"] = source_report_files
    grouped_payload.pop("report_file", None)

    return K6ServiceExtractionRun(
        source_report_files=source_report_files,
        extracted=_to_final_run_payload(grouped_payload),
    )


def _to_symbolstreeservice_metrics(run: BaseModel) -> SymbolstreeserviceExtractedMetrics:
    """Convert a generic extracted model into symbolstreeservice metrics."""
    if not hasattr(run, "scenario") or not hasattr(run, "report_file"):
        msg = "Post-processing requires symbolstreeservice extracted metrics"
        raise TypeError(msg)
    return cast("SymbolstreeserviceExtractedMetrics", run)


def _merge_trend_metric_values(
    *,
    extracted_runs: list[SymbolstreeserviceExtractedMetrics],
    field_name: str,
    total_iterations: int,
) -> dict[str, float]:
    """Merge trend metric values using weighted averages and guardrail percentiles."""
    weights = [run.iterations.count for run in extracted_runs]
    values = [getattr(run, field_name) for run in extracted_runs]
    return {
        "min": min(value.min for value in values),
        "avg": _weighted_average(
            values=[value.avg for value in values],
            weights=weights,
            fallback_divisor=total_iterations,
        ),
        "med": _weighted_average(
            values=[value.med for value in values],
            weights=weights,
            fallback_divisor=total_iterations,
        ),
        "max": max(value.max for value in values),
        "p(95)": max(value.p95 for value in values),
        "p(99)": max(value.p99 for value in values),
    }


def _merge_rate_metric_values(
    *,
    extracted_runs: list[SymbolstreeserviceExtractedMetrics],
    field_name: str,
) -> dict[str, float | int]:
    """Merge rate metric values from summed pass/fail counts."""
    values = [getattr(run, field_name) for run in extracted_runs]
    passes = sum(value.passes for value in values)
    fails = sum(value.fails for value in values)
    total = passes + fails
    rate = fails / total if total else 0.0
    return {
        "rate": rate,
        "passes": passes,
        "fails": fails,
    }


def _merge_counter_metric_values(
    *,
    extracted_runs: list[SymbolstreeserviceExtractedMetrics],
    field_name: str,
) -> dict[str, float | int]:
    """Merge counter metric values by summing counts and rates."""
    values = [getattr(run, field_name) for run in extracted_runs]
    return {
        "count": sum(value.count for value in values),
        "rate": sum(value.rate for value in values),
    }


def _merge_optional_counter_metric_values(
    *,
    extracted_runs: list[SymbolstreeserviceExtractedMetrics],
    field_name: str,
) -> dict[str, float | int] | None:
    """Merge optional counter metric values when present in any source run."""
    values = [getattr(run, field_name) for run in extracted_runs]
    present_values = [value for value in values if value is not None]
    if not present_values:
        return None
    return {
        "count": sum(value.count for value in present_values),
        "rate": sum(value.rate for value in present_values),
    }


def _merge_thresholds(
    *,
    name: str,
    extracted_runs: list[SymbolstreeserviceExtractedMetrics],
) -> dict[str, list[str]]:
    """Merge threshold definitions under the grouped scenario name."""
    merged_thresholds: dict[str, list[str]] = {}
    for run in extracted_runs:
        for key, values in run.thresholds.items():
            normalized_key = _GROUPED_SCENARIO_NAME_FRAGMENT_PATTERN.sub(name, key)
            merged_thresholds.setdefault(normalized_key, [])
            for value in values:
                if value not in merged_thresholds[normalized_key]:
                    merged_thresholds[normalized_key].append(value)
    return merged_thresholds


def _weighted_average(*, values: list[float], weights: list[int], fallback_divisor: int) -> float:
    """Calculate a weighted average with a deterministic zero fallback."""
    weighted_sum = sum(value * weight for value, weight in zip(values, weights, strict=True))
    if fallback_divisor <= 0:
        return 0.0
    return weighted_sum / fallback_divisor


def _to_final_run_payload(payload: dict[str, object]) -> dict[str, object]:
    """Remove internal extraction-only fields from final run payloads."""
    final_payload = dict(payload)
    final_payload.pop("report_file", None)
    return final_payload
