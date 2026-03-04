"""Use case for deterministic service-specific k6 metric extraction."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel, ValidationError

from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6ServiceExtractionRun, VerificationMismatch
from qa_report_generator.application.service_definitions import get_service_definition
from qa_report_generator.domain.exceptions import ConfigurationError, ExtractionVerificationError

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.ports.output import StructuredLlmPort
    from qa_report_generator.application.service_definitions.base import ServiceDefinition


class K6ServiceExtractionService:
    """Extract deterministic structured metrics for one service from a k6 summary JSON."""

    def __init__(self, *, llm: StructuredLlmPort) -> None:
        """Store adapter dependencies."""
        self._llm = llm

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Run two-step extraction + verification and return validated payloads."""
        if not report_paths:
            msg = "No report files provided for extraction"
            raise ConfigurationError(msg, suggestion="Pass one or more k6 JSON reports")

        definition = self._resolve_definition(service)
        extracted_runs: list[K6ServiceExtractionRun] = []

        for report_path in report_paths:
            source = self._load_source_json(report_path)
            filtered_source = self._filter_source(source, remove_keys=definition.remove_keys)
            filtered_source_json = self._to_canonical_json(filtered_source)

            extraction_prompt = definition.build_extraction_user_prompt(
                filtered_source_json,
                definition.dump_schema(),
                report_path.name,
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

            extracted_runs.append(K6ServiceExtractionRun(report_file=report_path.name, extracted=extracted))

        return K6ServiceExtractionResult(
            service=service,
            extracted_runs=extracted_runs,
        )

    def _resolve_definition(self, service: str) -> ServiceDefinition:
        try:
            return get_service_definition(service)
        except ValueError as err:
            msg = f"Unsupported service '{service}'"
            raise ConfigurationError(msg, suggestion="Add service definition module and register it") from err

    def _load_source_json(self, report_path: Path) -> dict[str, Any]:
        try:
            return cast("dict[str, Any]", json.loads(report_path.read_text(encoding="utf-8")))
        except json.JSONDecodeError as err:
            msg = f"Invalid JSON in report: {report_path}"
            raise ConfigurationError(msg, suggestion="Check k6 artifact validity") from err

    def _filter_source(self, source: dict[str, Any], *, remove_keys: frozenset[str]) -> dict[str, Any]:
        filtered: dict[str, Any] = {}
        for key, value in source.items():
            if key in remove_keys:
                continue
            filtered[key] = value
        return filtered

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
