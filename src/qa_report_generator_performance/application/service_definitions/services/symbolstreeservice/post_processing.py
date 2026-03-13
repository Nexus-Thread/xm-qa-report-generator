"""Post-processing for derived symbolstreeservice outputs."""

from __future__ import annotations

import re
from collections import defaultdict
from copy import deepcopy
from typing import Any, cast

from qa_report_generator_performance.application.service_definitions.services.symbolstreeservice.schema import (
    SymbolstreeserviceExtractedMetrics,
)
from qa_report_generator_performance.application.service_definitions.shared import (
    derive_merge_buckets,
    merge_counter_metric_field,
    merge_optional_counter_metric_field,
    merge_rate_metric_field,
    merge_trend_metric_field,
)
from qa_report_generator_performance.application.service_definitions.shared.base import PreparedExtractionRun

_GROUPED_SCENARIO_PATTERN = re.compile(r"^(?P<base>getSymbolsTreeInfo)\d+$")
_GROUPED_SCENARIO_NAME_FRAGMENT_PATTERN = re.compile(r"getSymbolsTreeInfo\d+")

_MERGE_BUCKETS = derive_merge_buckets(SymbolstreeserviceExtractedMetrics)


def build_post_processed_runs(
    extracted_runs: list[PreparedExtractionRun],
) -> list[PreparedExtractionRun]:
    """Build grouped prepared runs for numbered getSymbolsTreeInfo scenarios."""
    passthrough_runs: list[PreparedExtractionRun] = []
    grouped_runs: dict[str, list[PreparedExtractionRun]] = defaultdict(list)

    for extracted_run in extracted_runs:
        match = _GROUPED_SCENARIO_PATTERN.match(_scenario_name(_to_symbolstreeservice_metrics(extracted_run.extracted)))
        if match is None:
            passthrough_runs.append(extracted_run)
            continue
        grouped_runs[match.group("base")].append(extracted_run)

    merged_runs = [_build_grouped_run(name=group_name, extracted_runs=group_runs) for group_name, group_runs in sorted(grouped_runs.items())]
    return sorted(
        [*passthrough_runs, *merged_runs],
        key=_prepared_run_scenario_name,
    )


def _build_grouped_run(
    *,
    name: str,
    extracted_runs: list[PreparedExtractionRun],
) -> PreparedExtractionRun:
    """Build one grouped prepared run from multiple extracted runs."""
    typed_runs = [_to_symbolstreeservice_metrics(run.extracted) for run in extracted_runs]
    representative_run = typed_runs[0]
    source_report_files = tuple(sorted(source_report_file for prepared_run in extracted_runs for source_report_file in prepared_run.source_report_files))
    duration_values = {float(run.test_run_duration_ms) for run in typed_runs}

    grouped_payload = deepcopy(representative_run.model_dump(by_alias=True))
    grouped_payload["scenario"] = {
        **_required_dict(grouped_payload, "scenario"),
        "name": name,
        "rate": sum(_scenario_float(run, "rate") for run in typed_runs),
        "preAllocatedVUs": max(_scenario_int(run, "preAllocatedVUs", "pre_allocated_vus") for run in typed_runs),
        "maxVUs": max(_scenario_int(run, "maxVUs", "max_vus") for run in typed_runs),
    }
    grouped_payload["test_run_duration_ms"] = duration_values.pop() if len(duration_values) == 1 else max(float(run.test_run_duration_ms) for run in typed_runs)
    grouped_payload["thresholds"] = _merge_thresholds(name=name, extracted_runs=typed_runs)
    grouped_payload["threshold_statuses"] = _merge_threshold_statuses(
        name=name,
        extracted_runs=typed_runs,
    )
    for field_name in _MERGE_BUCKETS.trend_fields:
        grouped_payload[field_name] = merge_trend_metric_field(
            extracted_runs=typed_runs,
            field_name=field_name,
        )
    for field_name in _MERGE_BUCKETS.rate_fields:
        grouped_payload[field_name] = merge_rate_metric_field(
            extracted_runs=typed_runs,
            field_name=field_name,
        )
    for field_name in _MERGE_BUCKETS.counter_fields:
        grouped_payload[field_name] = merge_counter_metric_field(
            extracted_runs=typed_runs,
            field_name=field_name,
        )
    for field_name in _MERGE_BUCKETS.optional_counter_fields:
        grouped_payload[field_name] = merge_optional_counter_metric_field(
            extracted_runs=typed_runs,
            field_name=field_name,
        )
    grouped_payload["source_scenarios"] = [_scenario_name(run) for run in typed_runs]
    grouped_payload["group_size"] = len(extracted_runs)
    grouped_payload["report_file"] = source_report_files[0]

    return PreparedExtractionRun(
        source_report_files=source_report_files,
        extracted=SymbolstreeserviceExtractedMetrics.model_validate(grouped_payload),
    )


def _to_symbolstreeservice_metrics(run: object) -> SymbolstreeserviceExtractedMetrics:
    """Convert a generic extracted model into symbolstreeservice metrics."""
    if not hasattr(run, "scenario") or not hasattr(run, "report_file"):
        msg = "Post-processing requires symbolstreeservice extracted metrics"
        raise TypeError(msg)
    return cast("SymbolstreeserviceExtractedMetrics", run)


def _prepared_run_scenario_name(run: PreparedExtractionRun) -> str:
    """Return scenario name for sorting prepared runs."""
    return _scenario_name(_to_symbolstreeservice_metrics(run.extracted))


def _merge_thresholds(
    *,
    name: str,
    extracted_runs: list[SymbolstreeserviceExtractedMetrics],
) -> dict[str, list[str]]:
    """Merge threshold definitions under the grouped scenario name."""
    merged_thresholds: dict[str, list[str]] = {}
    for run in extracted_runs:
        for key, values in run.thresholds.items():
            if not isinstance(key, str) or not isinstance(values, list):
                continue
            normalized_key = _GROUPED_SCENARIO_NAME_FRAGMENT_PATTERN.sub(name, key)
            merged_thresholds.setdefault(normalized_key, [])
            for value in values:
                if not isinstance(value, str):
                    continue
                if value not in merged_thresholds[normalized_key]:
                    merged_thresholds[normalized_key].append(value)
    return merged_thresholds


def _merge_threshold_statuses(
    *,
    name: str,
    extracted_runs: list[SymbolstreeserviceExtractedMetrics],
) -> dict[str, dict[str, bool]]:
    """Merge threshold ok-status values under the grouped scenario name."""
    merged_results: dict[tuple[str, str], bool] = {}
    for run in extracted_runs:
        for metric_key, threshold_map in run.threshold_statuses.items():
            if not isinstance(metric_key, str) or not isinstance(threshold_map, dict):
                continue
            for expression, ok in threshold_map.items():
                if not isinstance(expression, str) or not isinstance(ok, bool):
                    continue
                normalized_metric_key = _GROUPED_SCENARIO_NAME_FRAGMENT_PATTERN.sub(name, metric_key)
                existing_status = merged_results.get((normalized_metric_key, expression))
                merged_results[(normalized_metric_key, expression)] = _merge_threshold_ok(existing_status, ok)
    normalized_results: dict[str, dict[str, bool]] = {}
    for (metric_key, expression), ok in sorted(merged_results.items()):
        normalized_results.setdefault(metric_key, {})[expression] = ok
    return normalized_results


def _merge_threshold_ok(existing_status: bool | None, new_status: bool) -> bool:
    """Merge threshold ok-status values with failures taking precedence."""
    return not (existing_status is False or new_status is False)


def _scenario_name(run: SymbolstreeserviceExtractedMetrics) -> str:
    """Return the extracted scenario name from one prepared run."""
    return run.scenario.name


def _scenario_int(run: SymbolstreeserviceExtractedMetrics, *field_names: str) -> int:
    """Return one required integer scenario field from a prepared run."""
    scenario = run.scenario.model_dump(by_alias=True)
    for field_name in field_names:
        value = scenario.get(field_name)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    msg = f"Prepared symbolstreeservice run is missing scenario fields: {', '.join(field_names)}"
    raise TypeError(msg)


def _scenario_float(run: SymbolstreeserviceExtractedMetrics, *field_names: str) -> float:
    """Return one required numeric scenario field from a prepared run."""
    scenario = run.scenario.model_dump(by_alias=True)
    for field_name in field_names:
        value = scenario.get(field_name)
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
    msg = f"Prepared symbolstreeservice run is missing scenario fields: {', '.join(field_names)}"
    raise TypeError(msg)


def _required_dict(payload: dict[str, Any], field_name: str) -> dict[str, Any]:
    """Return one required object field from a payload."""
    value = payload.get(field_name)
    if isinstance(value, dict):
        return value
    msg = f"Prepared symbolstreeservice payload is missing object field: {field_name}"
    raise TypeError(msg)


def _required_int(payload: dict[str, Any], field_name: str) -> int:
    """Return one required integer field from a payload."""
    value = payload.get(field_name)
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    msg = f"Prepared symbolstreeservice payload is missing integer field: {field_name}"
    raise TypeError(msg)


def _required_float(payload: dict[str, Any], field_name: str) -> float:
    """Return one required numeric field from a payload."""
    value = payload.get(field_name)
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    msg = f"Prepared symbolstreeservice payload is missing numeric field: {field_name}"
    raise TypeError(msg)
