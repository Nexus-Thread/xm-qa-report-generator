"""Scenario extraction pipeline for service-specific k6 extraction."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qa_report_generator_performance.application.exceptions import ExtractionVerificationError

from .json_utils import to_canonical_json
from .scenario_verification import verify_extracted_payload
from .schema_validation import validate_with_schema

if TYPE_CHECKING:
    from pydantic import BaseModel

    from qa_report_generator_performance.application.ports.output import StructuredLlmPort
    from qa_report_generator_performance.application.service_definitions.shared.base import ServiceDefinition
    from qa_report_generator_performance.domain.analytics import K6Scenario

LOGGER = logging.getLogger(__name__)


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
    max_verification_attempts: int = 3,
) -> ExtractedRunModel:
    """Extract, validate, and verify one scenario payload."""
    if max_verification_attempts < 1:
        msg = "max_verification_attempts must be greater than or equal to 1"
        raise ValueError(msg)

    filtered_source_json = to_canonical_json(scenario.source_payload)
    last_error: ExtractionVerificationError | None = None

    for attempt in range(1, max_verification_attempts + 1):
        extracted_model = _extract_payload(
            llm=llm,
            scenario=scenario,
            definition=definition,
            schema=schema,
            filtered_source_json=filtered_source_json,
        )
        try:
            verify_extracted_payload(
                llm=llm,
                scenario=scenario,
                definition=definition,
                schema=schema,
                extracted=extracted_model.model_dump(by_alias=True),
            )
        except ExtractionVerificationError as err:
            last_error = err
            if attempt == max_verification_attempts:
                break
            LOGGER.warning(
                "Verification failed; retrying extraction",
                extra={
                    "component": "scenario_extraction",
                    "scenario_name": scenario.name,
                    "source_report_file": scenario.source_report_file,
                    "attempt": attempt,
                    "max_verification_attempts": max_verification_attempts,
                },
            )
            continue

        return ExtractedRunModel(
            source_report_file=scenario.source_report_file,
            source_payload=scenario.source_payload,
            extracted=extracted_model,
        )

    if last_error is None:
        msg = "Verification retry flow terminated without a verification error"
        raise RuntimeError(msg)

    raise _build_retry_exhausted_error(
        error=last_error,
        scenario=scenario,
        max_verification_attempts=max_verification_attempts,
    ) from last_error


def _build_retry_exhausted_error(
    *,
    error: ExtractionVerificationError,
    scenario: K6Scenario,
    max_verification_attempts: int,
) -> ExtractionVerificationError:
    """Return a verification error augmented with exhausted retry context."""
    return ExtractionVerificationError(
        (
            "Verification failed after exhausting extraction retries for "
            f"{scenario.name} ({scenario.source_report_file}) after {max_verification_attempts} attempts. "
            f"Last error: {error}"
        ),
        suggestion=error.suggestion,
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
