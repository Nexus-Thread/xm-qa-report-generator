"""Use case for deterministic service-specific k6 metric extraction."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6ServiceExtractionRun, VerificationMismatch
from qa_report_generator.application.service_definitions import get_service_definition
from qa_report_generator.domain.exceptions import ConfigurationError, ExtractionVerificationError

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.ports.output import K6ParsedReportParserPort, StructuredLlmPort
    from qa_report_generator.application.service_definitions.base import ServiceDefinition
    from qa_report_generator.domain.analytics import K6ParsedReport


class K6ServiceExtractionService:
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

        definition = self._resolve_definition(service)
        remove_keys = definition.remove_keys if definition is not None else frozenset()
        parsed_report = self._parser.parse(
            service=service,
            report_files=report_paths,
            remove_keys=remove_keys,
        )

        if definition is None:
            return self._build_generic_result(parsed_report)

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
            filtered_source_json = self._to_canonical_json(scenario.raw_payload)

            extraction_prompt = definition.build_extraction_user_prompt(
                filtered_source_json,
                definition.dump_schema(),
                scenario.source_report_file,
            )
            extracted_payload = self._llm.complete_json(
                system_prompt=definition.extraction_system_prompt,
                user_prompt=extraction_prompt,
            )

            extracted_model = self._validate_with_schema(definition.schema_model, extracted_payload)
            if definition.validate_extracted is not None:
                definition.validate_extracted(extracted_model)

            extracted = extracted_model.model_dump(by_alias=True)
            extracted_json = self._to_canonical_json(extracted)
            verification_prompt = definition.build_verification_user_prompt(filtered_source_json, extracted_json)
            verification_payload = self._llm.complete_json(
                system_prompt=definition.verification_system_prompt,
                user_prompt=verification_prompt,
            )
            mismatches = self._parse_mismatches(verification_payload)
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

    def _resolve_definition(self, service: str) -> ServiceDefinition | None:
        try:
            return get_service_definition(service)
        except ValueError:
            return None

    def _build_generic_result(self, parsed_report: K6ParsedReport) -> K6ServiceExtractionResult:
        """Build generic parsed output when no service definition exists."""
        extracted_runs = [
            K6ServiceExtractionRun(
                report_file=scenario.source_report_file,
                extracted={
                    "service": parsed_report.service,
                    "scenario": {
                        "name": scenario.name,
                        "env_name": scenario.env_name,
                        "executor": scenario.executor,
                        "rate": scenario.rate,
                        "duration": scenario.duration,
                        "pre_allocated_vus": scenario.pre_allocated_vus,
                        "max_vus": scenario.max_vus,
                    },
                    "test_run_duration_ms": scenario.test_run_duration_ms,
                    "thresholds": scenario.thresholds,
                    "metrics": scenario.metrics,
                },
            )
            for scenario in parsed_report.scenarios
        ]
        return K6ServiceExtractionResult(
            service=parsed_report.service,
            mode="generic",
            extracted_runs=extracted_runs,
        )

    def _to_canonical_json(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def _validate_with_schema(self, schema_type: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
        try:
            return schema_type.model_validate(payload)
        except ValidationError as err:
            msg = "Extracted payload failed schema validation"
            raise ExtractionVerificationError(msg, suggestion=str(err)) from err

    def _parse_mismatches(self, verification_payload: dict[str, Any]) -> list[VerificationMismatch]:
        raw_mismatches = verification_payload.get("mismatches", [])
        if not isinstance(raw_mismatches, list):
            msg = "Verification response is missing mismatches array"
            raise ExtractionVerificationError(msg, suggestion="Ensure verifier prompt returns expected JSON shape")

        mismatches: list[VerificationMismatch] = []
        for raw in raw_mismatches:
            if not isinstance(raw, dict):
                continue
            mismatches.append(
                VerificationMismatch(
                    field=str(raw.get("field", "")),
                    expected=str(raw.get("expected", "")),
                    actual=str(raw.get("actual", "")),
                    source_jsonpath=str(raw.get("source_jsonpath", "")),
                    extracted_jsonpath=str(raw.get("extracted_jsonpath", "")),
                    reason=str(raw.get("reason", "")),
                )
            )
        return mismatches
