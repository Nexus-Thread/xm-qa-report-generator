"""Verification helpers for k6 service extraction use case."""

from __future__ import annotations

from typing import Any

from qa_report_generator.application.dtos import JsonScalar, VerificationMismatch
from qa_report_generator.domain.exceptions import ExtractionVerificationError


def _is_false_positive_mismatch(raw: dict[str, Any]) -> bool:
    """Return true when verifier reported a successful comparison as a mismatch."""
    expected = raw.get("expected")
    actual = raw.get("actual")
    reason = str(raw.get("reason", "")).lower()

    if expected == actual:
        return True
    if "value matches" in reason:
        return True

    source_jsonpath = str(raw.get("source_jsonpath", ""))
    tagged_metric_required = "scenario-tagged" in reason or "tagged metric" in reason
    untagged_http_req_failed_path = "metrics.http_req_failed.values" in source_jsonpath
    tagged_http_req_failed_path = "metrics.http_req_failed{" in source_jsonpath

    return tagged_metric_required and untagged_http_req_failed_path and not tagged_http_req_failed_path


def _coerce_json_scalar(value: Any) -> JsonScalar:
    """Return a JSON-scalar value or a stringified fallback."""
    if isinstance(value, bool | int | float | str) or value is None:
        return value
    return str(value)


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
        if _is_false_positive_mismatch(raw):
            continue
        mismatches.append(
            VerificationMismatch(
                field=str(raw.get("field", "")),
                expected=_coerce_json_scalar(raw.get("expected")),
                actual=_coerce_json_scalar(raw.get("actual")),
                source_jsonpath=str(raw.get("source_jsonpath", "")),
                extracted_jsonpath=str(raw.get("extracted_jsonpath", "")),
                reason=str(raw.get("reason", "")),
            )
        )
    return mismatches
