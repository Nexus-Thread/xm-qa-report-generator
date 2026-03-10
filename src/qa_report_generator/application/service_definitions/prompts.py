"""Shared prompt builders for service-specific k6 extraction."""

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
            "When both generic and scenario-tagged metrics exist, prefer only the exact test_name:<scenario> tagged metric for the selected scenario.",
            "Ignore other tagged variants that do not use test_name:<scenario>; if no exact scenario-tagged metric exists, use the generic metric.",
            "If the schema names an exact tagged metric key, use that exact metric entry and do not use a generic sibling metric with the same base name.",
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
            "Return entries in mismatches only when expected and actual differ, or when a required verification target is missing.",
            "Do not include successful comparisons, confirmations, or informational notes in mismatches.",
            "If a field matches exactly, do not mention it in the response.",
            "Never emit a mismatches entry whose expected and actual values are equal.",
            "Never emit explanatory notes such as 'no mismatch', 'matches', or other success wording inside mismatches.",
            "Use target_schema field descriptions as the source of truth for where each extracted field must be verified from.",
            "If target_schema describes a field as coming from verification_context, verify it against verification_context rather than source JSON.",
            "Do not report a mismatch for context-backed fields solely because they are absent from source JSON.",
            "If target_schema allows null for a field and the schema-authorized source path is absent, treat null as correct rather than as a mismatch.",
            "Do not report a mismatch when an optional metric object is absent in source and the extracted value is null.",
            "When multiple candidate source values exist, prefer the source location described by the schema guidance.",
            "If the schema describes a tagged metric key, treat that exact tagged metric entry as the only authorized source and do not substitute a generic sibling metric with the same base name.",
            "If a tagged metric exists for the selected scenario, never use an untagged sibling metric as expected/source_jsonpath/reason for that extracted field.",
            "Treat only exact test_name:<scenario> tagged metrics as scenario-tagged candidates for preference.",
            "Do not use unrelated tagged variants such as other tag combinations when schema guidance says to prefer scenario-tagged metrics.",
            "If no exact test_name:<scenario> tagged metric exists, use the untagged generic metric rather than another tagged variant.",
            "Keep mismatch reasoning and source_jsonpath consistent with the same schema-authorized source path.",
            "Do not return a mismatch whose reason says a tagged metric should be used while source_jsonpath points to an untagged sibling metric.",
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


__all__ = [
    "EXTRACTION_SYSTEM_PROMPT",
    "VERIFICATION_SYSTEM_PROMPT",
    "build_extraction_user_prompt",
    "build_verification_user_prompt",
]
