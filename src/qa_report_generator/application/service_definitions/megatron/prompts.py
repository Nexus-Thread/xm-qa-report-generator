"""Prompt builders for megatron extraction and verification."""

from __future__ import annotations

import json
from typing import Any

EXTRACTION_SYSTEM_PROMPT = (
    "You extract structured k6 metrics for service 'megatron'. "
    "Return only JSON object that matches the provided schema. "
    "All numeric values must be copied exactly from source without rounding."
)

VERIFICATION_SYSTEM_PROMPT = (
    "You verify extracted k6 metrics against source JSON. "
    "Return JSON with key 'mismatches' list. "
    "Each mismatch item must include: field, expected, actual, source_jsonpath, extracted_jsonpath, reason."
)


def build_extraction_user_prompt(filtered_source_json: str, schema: dict[str, Any], report_file: str) -> str:
    """Build extraction user prompt payload."""
    payload = {
        "task": "extract_megatron_metrics",
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


def build_verification_user_prompt(filtered_source_json: str, extracted_json: str) -> str:
    """Build verification user prompt payload."""
    payload = {
        "task": "verify_megatron_extraction",
        "source": json.loads(filtered_source_json),
        "extracted": json.loads(extracted_json),
        "rules": [
            "Compare all numeric fields exactly.",
            "Ignore minor wording differences in optional text fields.",
            "Return mismatches for missing or wrong fields with JSONPath references.",
            "Do not compare extracted fields against whole metric objects such as $.source.metrics.<metric>; compare against concrete leaf values only.",
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
