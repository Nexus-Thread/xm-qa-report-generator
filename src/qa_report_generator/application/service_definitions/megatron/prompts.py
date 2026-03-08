"""Prompt builders for k6 extraction and verification."""

from __future__ import annotations

import json
from typing import Any

EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured k6 metrics from a filtered k6 JSON report. "
    "Return only a JSON object that matches the provided schema. "
    "Copy all numeric values exactly from the source without rounding or reformatting."
)

VERIFICATION_SYSTEM_PROMPT = (
    "You verify extracted k6 metrics against the source JSON. "
    "Return only a JSON object with a single key: mismatches. "
    'If the extraction is correct, return {"mismatches": []}. '
    "Each mismatch must include: field, expected, actual, source_jsonpath, extracted_jsonpath, and reason."
)


def build_extraction_user_prompt(filtered_source_json: str, schema: dict[str, Any], report_file: str) -> str:
    """Build extraction user prompt payload."""
    payload = {
        "task": "extract_k6_metrics",
        "report_file": report_file,
        "instructions": [
            "Use scenario-specific metrics by selecting the scenario in execScenarios keys.",
            "When both generic and scenario-tagged metrics exist, prefer scenario-tagged keys.",
            "Keep thresholds exactly as provided.",
        ],
        "target_schema": schema,
        "source": json.loads(filtered_source_json),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_verification_user_prompt(
    filtered_source_json: str,
    extracted_json: str,
    schema: dict[str, Any],
    verification_context: dict[str, Any],
) -> str:
    """Build verification user prompt payload."""
    payload = {
        "task": "verify_k6_extraction",
        "target_schema": schema,
        "verification_context": verification_context,
        "source": json.loads(filtered_source_json),
        "extracted": json.loads(extracted_json),
        "rules": [
            "Compare numeric values exactly.",
            "Treat missing required fields as mismatches.",
            "Ignore minor wording differences only in optional text fields.",
            "Use target_schema field descriptions as the source of truth for where each extracted field must be verified from.",
            "If target_schema describes a field as coming from verification_context, verify it against verification_context rather than source JSON.",
            "Do not report a mismatch for context-backed fields solely because they are absent from source JSON.",
            "If target_schema allows null for a field and the schema-authorized source path is absent, treat null as correct rather than as a mismatch.",
            "Do not report a mismatch when an optional metric object is absent in source and the extracted value is null.",
            "When multiple candidate source values exist, prefer the source location described by the schema guidance.",
            "Do not treat unrelated duplicate source fields as mismatches if the extracted value matches the schema-authorized source field.",
            "For scenario fields, verify against the selected scenario entry rather than similarly named values elsewhere in the payload.",
            "For every mismatch, return the exact source and extracted JSONPath of the compared leaf values.",
            "Compare extracted fields only to concrete leaf values, never to whole metric objects such as $.source.metrics.<metric>.",
            "Do not infer, normalize, or reinterpret values.",
        ],
        "response_schema": {
            "mismatches": [
                {
                    "field": "string",
                    "expected": "string",
                    "actual": "string",
                    "source_jsonpath": "string",
                    "extracted_jsonpath": "string",
                    "reason": "string",
                }
            ]
        },
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
