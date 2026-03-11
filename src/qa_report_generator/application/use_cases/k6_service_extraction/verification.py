"""Verification helpers for k6 service extraction use case."""

from __future__ import annotations

import re
from typing import Any

from qa_report_generator.application.dtos import JsonScalar, VerificationMismatch
from qa_report_generator.application.exceptions import ExtractionVerificationError

SUCCESS_REASON_MARKERS = (
    "value matches",
    "no mismatch",
    "matches the schema-authorized",
    "matches the schema authorized",
)

NON_SCENARIO_TAGGED_REASON_MARKERS = (
    "the only tagged",
    "additional tagged variant",
)
_JSON_PATH_TOKEN_PATTERN = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)|\[\"([^\"]+)\"\]")


def _is_false_positive_mismatch(raw: dict[str, Any]) -> bool:
    """Return true when verifier reported a successful comparison as a mismatch."""
    expected = raw.get("expected")
    actual = raw.get("actual")
    reason = str(raw.get("reason", "")).lower()

    if expected == actual:
        return True
    if any(marker in reason for marker in SUCCESS_REASON_MARKERS):
        return True

    source_jsonpath = str(raw.get("source_jsonpath", ""))
    extracted_jsonpath = str(raw.get("extracted_jsonpath", ""))
    tagged_metric_required = "scenario-tagged" in reason or "tagged metric" in reason
    untagged_http_req_failed_path = "metrics.http_req_failed.values" in source_jsonpath
    tagged_http_req_failed_path = "metrics.http_req_failed{" in source_jsonpath

    if (
        tagged_metric_required
        and any(marker in reason for marker in NON_SCENARIO_TAGGED_REASON_MARKERS)
        and "{expected_response:true}" in source_jsonpath
        and "$.extracted.http_req_duration" in extracted_jsonpath
    ):
        return True

    return tagged_metric_required and untagged_http_req_failed_path and not tagged_http_req_failed_path


def _is_payload_inconsistent_mismatch(
    raw: dict[str, Any],
    *,
    source_payload: dict[str, Any] | None,
    extracted_payload: dict[str, Any] | None,
) -> bool:
    """Return true when mismatch details contradict the concrete payload values."""
    if source_payload is None or extracted_payload is None:
        return False

    source_jsonpath = str(raw.get("source_jsonpath", ""))
    extracted_jsonpath = str(raw.get("extracted_jsonpath", ""))
    resolved_source = _resolve_json_path(source_payload, source_jsonpath, root_name="source")
    resolved_extracted = _resolve_json_path(extracted_payload, extracted_jsonpath, root_name="extracted")

    if resolved_source is _MISSING or resolved_extracted is _MISSING:
        return False

    return resolved_source == resolved_extracted


_MISSING = object()


def _resolve_json_path(payload: dict[str, Any], json_path: str, *, root_name: str) -> Any:
    """Resolve a limited JSONPath expression against a payload."""
    prefix = f"$.{root_name}"
    if not json_path.startswith(prefix):
        return _MISSING

    current: Any = payload
    for match in _JSON_PATH_TOKEN_PATTERN.finditer(json_path[len(prefix) :]):
        token = match.group(1) or match.group(2)
        if not isinstance(current, dict) or token not in current:
            return _MISSING
        current = current[token]
    return current


def _coerce_json_scalar(value: Any) -> JsonScalar:
    """Return a JSON-scalar value or a stringified fallback."""
    if isinstance(value, bool | int | float | str) or value is None:
        return value
    return str(value)


def parse_mismatches(
    verification_payload: dict[str, Any],
    *,
    source_payload: dict[str, Any] | None = None,
    extracted_payload: dict[str, Any] | None = None,
) -> list[VerificationMismatch]:
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
        if _is_payload_inconsistent_mismatch(
            raw,
            source_payload=source_payload,
            extracted_payload=extracted_payload,
        ):
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
