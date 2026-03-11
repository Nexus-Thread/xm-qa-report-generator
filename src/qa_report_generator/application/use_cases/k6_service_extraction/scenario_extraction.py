"""Scenario extraction pipeline for service-specific k6 extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qa_report_generator.domain.exceptions import MissingK6MetricError

from .json_utils import to_canonical_json
from .metric_selection import pick_metric
from .scenario_verification import verify_extracted_payload
from .schema_validation import validate_with_schema

if TYPE_CHECKING:
    from pydantic import BaseModel

    from qa_report_generator.application.ports.output import StructuredLlmPort
    from qa_report_generator.application.service_definitions.base import ServiceDefinition
    from qa_report_generator.domain.analytics import K6Scenario


@dataclass(frozen=True, slots=True)
class ExtractedRunModel:
    """Container for a validated extracted model and its source file."""

    source_report_file: str
    source_payload: dict[str, Any]
    extracted: BaseModel


def extract_verified_run_model(
    *,
    llm: StructuredLlmPort,
    scenario: K6Scenario,
    definition: ServiceDefinition,
    schema: dict[str, Any],
) -> ExtractedRunModel:
    """Extract, validate, and verify one scenario payload."""
    filtered_source_json = to_canonical_json(scenario.source_payload)
    extracted_model = _extract_payload(
        llm=llm,
        scenario=scenario,
        definition=definition,
        schema=schema,
        filtered_source_json=filtered_source_json,
    )
    verify_extracted_payload(
        llm=llm,
        scenario=scenario,
        definition=definition,
        schema=schema,
        extracted=extracted_model.model_dump(by_alias=True),
    )
    return ExtractedRunModel(
        source_report_file=scenario.source_report_file,
        source_payload=scenario.source_payload,
        extracted=extracted_model,
    )


def _extract_payload(
    *,
    llm: StructuredLlmPort,
    scenario: K6Scenario,
    definition: ServiceDefinition,
    schema: dict[str, Any],
    filtered_source_json: str,
) -> BaseModel:
    """Extract and validate one scenario payload."""
    extraction_prompt = definition.build_extraction_user_prompt(
        filtered_source_json,
        schema,
        scenario.source_report_file,
    )
    extracted_payload = llm.complete_json(
        system_prompt=definition.extraction_system_prompt,
        user_prompt=extraction_prompt,
    )
    extracted_payload = _apply_schema_authorized_metric_overrides(
        extracted_payload=extracted_payload,
        scenario=scenario,
    )

    extracted_model = validate_with_schema(definition.schema_model, extracted_payload)
    if definition.validate_extracted is not None:
        definition.validate_extracted(extracted_model)
    return extracted_model


def _apply_schema_authorized_metric_overrides(
    *,
    extracted_payload: dict[str, Any],
    scenario: K6Scenario,
) -> dict[str, Any]:
    """Override extracted metrics with schema-authorized scenario metric values."""
    normalized_payload = dict(extracted_payload)
    for metric_key in ("http_req_duration", "http_req_failed"):
        if metric_key not in normalized_payload:
            continue
        normalized_payload[metric_key] = pick_metric(
            scenario.source_payload,
            metric_key,
            scenario.name,
        ).get("values", normalized_payload[metric_key])

    normalized_payload["dropped_iterations"] = _pick_optional_metric_values(
        source=scenario.source_payload,
        metric_key="dropped_iterations",
        scenario_name=scenario.name,
        fallback=normalized_payload.get("dropped_iterations"),
    )

    return normalized_payload


def _pick_optional_metric_values(
    *,
    source: dict[str, Any],
    metric_key: str,
    scenario_name: str,
    fallback: Any,
) -> Any:
    """Return optional metric values from source when present, else fallback."""
    try:
        metric = pick_metric(source, metric_key, scenario_name)
    except MissingK6MetricError:
        return fallback

    return metric.get("values", fallback)
