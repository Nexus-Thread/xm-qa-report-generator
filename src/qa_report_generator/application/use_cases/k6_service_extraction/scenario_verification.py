"""Scenario verification pipeline for service-specific k6 extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qa_report_generator.application.exceptions import ExtractionVerificationError

from .json_utils import to_canonical_json
from .verification import parse_mismatches

if TYPE_CHECKING:
    from qa_report_generator.application.dtos import VerificationMismatch
    from qa_report_generator.application.ports.output import StructuredLlmPort
    from qa_report_generator.application.service_definitions.shared.base import ServiceDefinition
    from qa_report_generator.domain.analytics import K6Scenario


def verify_extracted_payload(
    *,
    llm: StructuredLlmPort,
    scenario: K6Scenario,
    definition: ServiceDefinition,
    schema: dict[str, Any],
    extracted: dict[str, Any],
) -> None:
    """Verify one extracted payload against the filtered source."""
    filtered_source_json = to_canonical_json(scenario.source_payload)
    extracted_json = to_canonical_json(extracted)
    verification_prompt = definition.build_verification_user_prompt(
        filtered_source_json,
        extracted_json,
        schema,
        {
            "report_file": scenario.source_report_file,
            "selected_scenario_name": scenario.name,
        },
    )
    verification_payload = llm.complete_json(
        system_prompt=definition.verification_system_prompt,
        user_prompt=verification_prompt,
    )
    mismatches = parse_mismatches(
        verification_payload,
        source_payload=scenario.source_payload,
        extracted_payload=extracted,
    )
    if mismatches:
        raise build_verification_error(mismatches[0])


def build_verification_error(
    first_mismatch: VerificationMismatch,
) -> ExtractionVerificationError:
    """Build a stable verification failure with first mismatch details."""
    msg = (
        "Verification failed with numeric mismatches. "
        f"First mismatch: {first_mismatch.field} expected={first_mismatch.expected} "
        f"actual={first_mismatch.actual} source={first_mismatch.source_jsonpath}"
    )
    return ExtractionVerificationError(
        msg,
        suggestion="Inspect source and extracted payloads for mapping drift",
    )
