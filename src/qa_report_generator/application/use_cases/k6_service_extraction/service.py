"""Use case for deterministic service-specific k6 metric extraction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qa_report_generator.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
    VerificationMismatch,
)
from qa_report_generator.application.ports.input import ExtractK6ServiceMetricsUseCase
from qa_report_generator.application.service_definitions import get_optional_service_definition
from qa_report_generator.domain.exceptions import ConfigurationError, ExtractionVerificationError

from .json_utils import to_canonical_json
from .result_builders import build_generic_result
from .schema_validation import validate_with_schema
from .verification import parse_mismatches

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.ports.output import K6ParsedReportParserPort, StructuredLlmPort
    from qa_report_generator.application.service_definitions.base import ServiceDefinition
    from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario


class K6ServiceExtractionService(ExtractK6ServiceMetricsUseCase):
    """Extract deterministic structured metrics for one service from a k6 summary JSON."""

    def __init__(self, *, llm: StructuredLlmPort, parser: K6ParsedReportParserPort) -> None:
        """Store adapter dependencies."""
        self._llm = llm
        self._parser = parser

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Run two-step extraction + verification and return validated payloads."""
        if not report_paths:
            msg = "No report files provided for extraction"
            raise ConfigurationError(msg, suggestion="Pass one or more k6 JSON reports")

        definition = get_optional_service_definition(service)
        parsed_report = self._parse_report(
            service=service,
            report_paths=report_paths,
            definition=definition,
        )

        if definition is None:
            return build_generic_result(parsed_report=parsed_report)

        return self._extract_service_specific(parsed_report=parsed_report, definition=definition)

    def _parse_report(
        self,
        *,
        service: str,
        report_paths: list[Path],
        definition: ServiceDefinition | None,
    ) -> K6ParsedReport:
        """Parse source reports with service-specific key filtering."""
        remove_keys = definition.remove_keys if definition is not None else frozenset()
        return self._parser.parse(
            service=service,
            report_files=report_paths,
            remove_keys=remove_keys,
        )

    def _extract_service_specific(
        self,
        *,
        parsed_report: K6ParsedReport,
        definition: ServiceDefinition,
    ) -> K6ServiceExtractionResult:
        """Run service-specific extraction flow for parsed scenarios."""
        schema = definition.dump_schema()
        extracted_run_models = [
            self._extract_verified_run_model(
                scenario=scenario,
                definition=definition,
                schema=schema,
            )
            for scenario in parsed_report.scenarios
        ]
        extracted_runs = [
            K6ServiceExtractionRun(
                source_report_files=[run_model.source_report_file],
                extracted=_to_final_run_payload(run_model.extracted.model_dump(by_alias=True)),
            )
            for run_model in extracted_run_models
        ]
        final_runs = self._post_process_runs(
            definition=definition,
            fallback_runs=extracted_runs,
            extracted_models=[run_model.extracted for run_model in extracted_run_models],
        )

        return K6ServiceExtractionResult(
            service=parsed_report.service,
            mode="service_specific",
            runs=final_runs,
        )

    def _extract_verified_run_model(
        self,
        *,
        scenario: K6Scenario,
        definition: ServiceDefinition,
        schema: dict[str, Any],
    ) -> _ExtractedRunModel:
        """Extract, validate, and verify one scenario payload."""
        filtered_source_json = to_canonical_json(scenario.raw_payload)
        extracted_model = self._extract_payload(
            scenario=scenario,
            definition=definition,
            schema=schema,
            filtered_source_json=filtered_source_json,
        )
        self._verify_extraction(
            scenario=scenario,
            definition=definition,
            schema=schema,
            filtered_source_json=filtered_source_json,
            extracted=extracted_model.model_dump(by_alias=True),
        )
        return _ExtractedRunModel(
            source_report_file=scenario.source_report_file,
            extracted=extracted_model,
        )

    def _extract_payload(
        self,
        *,
        scenario: K6Scenario,
        definition: ServiceDefinition,
        schema: dict[str, Any],
        filtered_source_json: str,
    ) -> Any:
        """Extract and validate one scenario payload."""
        extraction_prompt = definition.build_extraction_user_prompt(
            filtered_source_json,
            schema,
            scenario.source_report_file,
        )
        extracted_payload = self._llm.complete_json(
            system_prompt=definition.extraction_system_prompt,
            user_prompt=extraction_prompt,
        )

        extracted_model = validate_with_schema(definition.schema_model, extracted_payload)
        if definition.validate_extracted is not None:
            definition.validate_extracted(extracted_model)
        return extracted_model

    def _post_process_runs(
        self,
        *,
        definition: ServiceDefinition,
        fallback_runs: list[K6ServiceExtractionRun],
        extracted_models: list[Any],
    ) -> list[K6ServiceExtractionRun]:
        """Build final runs after optional post-processing."""
        if definition.post_process_extracted is None:
            return fallback_runs
        return definition.post_process_extracted(extracted_models)

    def _verify_extraction(
        self,
        *,
        scenario: K6Scenario,
        definition: ServiceDefinition,
        schema: dict[str, Any],
        filtered_source_json: str,
        extracted: dict[str, Any],
    ) -> None:
        """Verify one extracted payload against the filtered source."""
        extracted_json = to_canonical_json(extracted)
        verification_prompt = definition.build_verification_user_prompt(
            filtered_source_json,
            extracted_json,
            schema,
            {"report_file": scenario.source_report_file},
        )
        verification_payload = self._llm.complete_json(
            system_prompt=definition.verification_system_prompt,
            user_prompt=verification_prompt,
        )
        mismatches = parse_mismatches(verification_payload)
        if mismatches:
            raise self._build_verification_error(mismatches[0])

    @staticmethod
    def _build_verification_error(first_mismatch: VerificationMismatch) -> ExtractionVerificationError:
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


@dataclass(frozen=True)
class _ExtractedRunModel:
    """Container for a validated extracted model and its source file."""

    source_report_file: str
    extracted: Any


def _to_final_run_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove internal extraction-only fields from final run payloads."""
    final_payload = dict(payload)
    final_payload.pop("report_file", None)
    return final_payload
