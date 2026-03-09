"""Unit tests for shared service definition prompt builders."""

from __future__ import annotations

import json

from qa_report_generator.application.service_definitions.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
    build_verification_user_prompt,
)


def test_build_extraction_user_prompt_returns_expected_shared_payload() -> None:
    """Shared extraction prompt builder returns stable JSON payload."""
    prompt = build_extraction_user_prompt(
        '{"metrics":{"checks":{"values":{"rate":1.0}}}}',
        {"type": "object"},
        "report.json",
    )

    payload = json.loads(prompt)

    assert payload["task"] == "extract_k6_metrics"
    assert payload["report_file"] == "report.json"
    assert payload["target_schema"] == {"type": "object"}
    assert payload["source"] == {"metrics": {"checks": {"values": {"rate": 1.0}}}}
    assert EXTRACTION_SYSTEM_PROMPT.startswith("You extract structured k6 metrics")


def test_build_verification_user_prompt_returns_expected_shared_payload() -> None:
    """Shared verification prompt builder returns stable JSON payload."""
    prompt = build_verification_user_prompt(
        '{"metrics":{"checks":{"values":{"rate":1.0}}}}',
        '{"checks":{"rate":1.0}}',
        {"type": "object"},
        {"report_file": "report.json"},
    )

    payload = json.loads(prompt)

    assert payload["task"] == "verify_k6_extraction"
    assert payload["verification_context"] == {"report_file": "report.json"}
    assert payload["source"] == {"metrics": {"checks": {"values": {"rate": 1.0}}}}
    assert payload["extracted"] == {"checks": {"rate": 1.0}}
    assert payload["response_schema"]["mismatches"][0]["reason"] == "string"
    assert VERIFICATION_SYSTEM_PROMPT.startswith("You verify extracted k6 metrics")
