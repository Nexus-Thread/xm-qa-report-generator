"""Use case for deterministic service-specific k6 metric extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6ServiceExtractionRun
from qa_report_generator.application.ports.input import ExtractK6ServiceMetricsUseCase
from qa_report_generator.domain.exceptions import ConfigurationError, ExtractionVerificationError

from .definition_resolver import resolve_service_definition
from .json_utils import to_canonical_json
from .result_builders import build_generic_result
from .schema_validation import validate_with_schema
from .verification import parse_mismatches

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.ports.output import K6ParsedReportParserPort, StructuredLlmPort
    from qa_report_generator.application.service_definitions.base import ServiceDefinition
    from qa_report_generator.domain.analytics import K6ParsedReport


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

        definition = resolve_service_definition(service)
        remove_keys = definition.remove_keys if definition is not None else frozenset()
        parsed_report = self._parser.parse(
            service=service,
            report_files=report_paths,
            remove_keys=remove_keys,
        )

        if definition is None:
            return build_generic_result(parsed_report=parsed_report)

        return self._extract_service_specific(parsed_report=parsed_report, definition=definition)

    def _extract_service_specific(
        self,
        *,
        parsed_report: K6ParsedReport,
        definition: ServiceDefinition,
    ) -> K6ServiceExtractionResult:
        """Run service-specific extraction flow for parsed scenarios."""
        extracted_runs: list[K6ServiceExtractionRun] = []

        for scenario in parsed_report.scenarios:
            filtered_source_json = to_canonical_json(scenario.raw_payload)

            extraction_prompt = definition.build_extraction_user_prompt(
                filtered_source_json,
                definition.dump_schema(),
                scenario.source_report_file,
            )
            extracted_payload = self._llm.complete_json(
                system_prompt=definition.extraction_system_prompt,
                user_prompt=extraction_prompt,
            )

            extracted_model = validate_with_schema(definition.schema_model, extracted_payload)
            if definition.validate_extracted is not None:
                definition.validate_extracted(extracted_model)

            extracted = extracted_model.model_dump(by_alias=True)
            extracted_json = to_canonical_json(extracted)
            verification_prompt = definition.build_verification_user_prompt(filtered_source_json, extracted_json)
            verification_payload = self._llm.complete_json(
                system_prompt=definition.verification_system_prompt,
                user_prompt=verification_prompt,
            )
            mismatches = parse_mismatches(verification_payload)
            if mismatches:
                first_mismatch = mismatches[0]
                msg = (
                    "Verification failed with numeric mismatches. "
                    f"First mismatch: {first_mismatch.field} expected={first_mismatch.expected} "
                    f"actual={first_mismatch.actual} source={first_mismatch.source_jsonpath}"
                )
                raise ExtractionVerificationError(msg, suggestion="Inspect source and extracted payloads for mapping drift")

            extracted_runs.append(K6ServiceExtractionRun(report_file=scenario.source_report_file, extracted=extracted))

        return K6ServiceExtractionResult(
            service=parsed_report.service,
            mode="service_specific",
            extracted_runs=extracted_runs,
        )
