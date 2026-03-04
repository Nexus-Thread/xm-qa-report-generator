"""Response parsing helpers for structured LLM outputs."""

from __future__ import annotations

import json
from typing import Any

from qa_report_generator.adapters.output.narrative.openai.response import OpenAIResponseError, extract_message_content
from qa_report_generator.domain.exceptions import ExtractionVerificationError


def extract_structured_content(response: object) -> str:
    """Extract textual content from an OpenAI response object."""
    try:
        return extract_message_content(response)
    except OpenAIResponseError as err:
        msg = "LLM response has missing content or invalid content shape"
        raise ExtractionVerificationError(msg, suggestion=str(err)) from err


def parse_json_object(content: str) -> dict[str, Any]:
    """Parse model content and require a top-level JSON object."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as err:
        msg = "LLM returned invalid JSON payload"
        raise ExtractionVerificationError(msg, suggestion="Inspect model output and prompts") from err
    if not isinstance(payload, dict):
        msg = "LLM payload must be a JSON object"
        raise ExtractionVerificationError(msg, suggestion="Ensure prompt requests top-level JSON object")
    return payload
