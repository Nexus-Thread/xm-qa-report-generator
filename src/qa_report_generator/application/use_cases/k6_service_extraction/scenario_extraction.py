"""Scenario extraction pipeline for service-specific k6 extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .json_utils import to_canonical_json
from .scenario_verification import verify_extracted_payload
from .schema_validation import validate_with_schema

if TYPE_CHECKING:
    from pydantic import BaseModel

    from qa_report_generator.application.ports.output import StructuredLlmPort
    from qa_report_generator.application.service_definitions.shared.base import ServiceDefinition
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
        scenario.name,
    )
    extracted_payload = llm.complete_json(
        system_prompt=definition.extraction_system_prompt,
        user_prompt=extraction_prompt,
    )

    extracted_model = validate_with_schema(definition.schema_model, extracted_payload)
    if definition.validate_extracted is not None:
        definition.validate_extracted(extracted_model)
    return extracted_model
