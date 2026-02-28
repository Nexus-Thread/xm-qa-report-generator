"""Structured JSON completion adapter using OpenAI transport."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from qa_report_generator.adapters.output.narrative.openai.response import OpenAIResponseError, extract_message_content
from qa_report_generator.domain.exceptions import ExtractionVerificationError

if TYPE_CHECKING:
    from qa_report_generator.adapters.output.narrative.openai.protocols import OpenAIClientProtocol


class OpenAIStructuredLlmAdapter:
    """Generate deterministic JSON objects through OpenAI chat completions."""

    def __init__(self, *, client: OpenAIClientProtocol, model: str) -> None:
        """Store transport client and model name."""
        self._client = client
        self._model = model

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return parsed JSON payload from model response."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = self._client.create_json_completion(model=self._model, messages=messages)
        content = self._extract_content(response)

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as err:
            msg = "LLM returned invalid JSON payload"
            raise ExtractionVerificationError(msg, suggestion="Inspect model output and prompts") from err
        if not isinstance(payload, dict):
            msg = "LLM payload must be a JSON object"
            raise ExtractionVerificationError(msg, suggestion="Ensure prompt requests top-level JSON object")
        return payload

    def _extract_content(self, response: object) -> str:
        try:
            return extract_message_content(response)
        except OpenAIResponseError as err:
            msg = "LLM response is missing content"
            raise ExtractionVerificationError(msg, suggestion=str(err)) from err
