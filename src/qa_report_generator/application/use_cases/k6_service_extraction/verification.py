"""Verification helpers for k6 service extraction use case."""

from __future__ import annotations

from typing import Any

from qa_report_generator.application.dtos import VerificationMismatch
from qa_report_generator.domain.exceptions import ExtractionVerificationError


def parse_mismatches(verification_payload: dict[str, Any]) -> list[VerificationMismatch]:
    """Parse verifier mismatches payload into DTOs."""
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
