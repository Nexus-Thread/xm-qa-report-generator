"""Structured JSON completion adapter using OpenAI transport."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from qa_report_generator.adapters.output.narrative.openai.response import OpenAIResponseError, extract_message_content
from qa_report_generator.domain.exceptions import ExtractionVerificationError

if TYPE_CHECKING:
    from qa_report_generator.adapters.output.narrative.openai.protocols import OpenAIClientProtocol
    from qa_report_generator.application.ports.output import DebugJsonWriterPort

LOGGER = logging.getLogger(__name__)
_MAX_LOG_PREVIEW_CHARS = 10_000


def _truncate_for_log(value: str, *, max_chars: int = _MAX_LOG_PREVIEW_CHARS) -> tuple[str, bool]:
    """Return truncated log preview and truncation flag."""
    if len(value) <= max_chars:
        return value, False
    return f"{value[:max_chars]}...[truncated]", True


class OpenAIStructuredLlmAdapter:
    """Generate deterministic JSON objects through OpenAI chat completions."""

    def __init__(
        self,
        *,
        client: OpenAIClientProtocol,
        model: str,
        debug_json_writer: DebugJsonWriterPort | None = None,
        debug_json_enabled: bool = False,
    ) -> None:
        """Store transport client and runtime configuration."""
        self._client = client
        self._model = model
        self._debug_json_writer = debug_json_writer
        self._debug_json_enabled = debug_json_enabled

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return parsed JSON payload from model response."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        request_payload = {"model": self._model, "messages": messages}
        self._write_debug_payload(label="request_payload", payload=request_payload)
        request_payload_json = json.dumps(request_payload, ensure_ascii=False)
        request_payload_preview, request_payload_truncated = _truncate_for_log(request_payload_json)
        LOGGER.debug(
            "Structured LLM request payload: %s",
            request_payload_preview,
            extra={
                "component": self.__class__.__name__,
                "model": self._model,
                "payload_length": len(request_payload_json),
                "payload_truncated": request_payload_truncated,
            },
        )

        response = self._client.create_json_completion(model=self._model, messages=messages)
        content = self._extract_content(response)
        self._write_debug_payload(label="response_content", payload={"content": content})
        response_preview, response_truncated = _truncate_for_log(content)
        LOGGER.debug(
            "Structured LLM response content: %s",
            response_preview,
            extra={
                "component": self.__class__.__name__,
                "model": self._model,
                "payload_length": len(content),
                "payload_truncated": response_truncated,
            },
        )

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as err:
            msg = "LLM returned invalid JSON payload"
            raise ExtractionVerificationError(msg, suggestion="Inspect model output and prompts") from err
        if not isinstance(payload, dict):
            msg = "LLM payload must be a JSON object"
            raise ExtractionVerificationError(msg, suggestion="Ensure prompt requests top-level JSON object")

        self._write_debug_payload(label="parsed_payload", payload=payload)
        parsed_payload_json = json.dumps(payload, ensure_ascii=False)
        parsed_payload_preview, parsed_payload_truncated = _truncate_for_log(parsed_payload_json)
        LOGGER.debug(
            "Structured LLM parsed JSON payload: %s",
            parsed_payload_preview,
            extra={
                "component": self.__class__.__name__,
                "model": self._model,
                "payload_keys": list(payload.keys()),
                "payload_length": len(parsed_payload_json),
                "payload_truncated": parsed_payload_truncated,
            },
        )
        return payload

    def _extract_content(self, response: object) -> str:
        try:
            return extract_message_content(response)
        except OpenAIResponseError as err:
            msg = "LLM response has missing content or invalid content shape"
            raise ExtractionVerificationError(msg, suggestion=str(err)) from err

    def _write_debug_payload(self, *, label: str, payload: Any) -> None:
        """Write debug payload if JSON debug output is enabled."""
        if not self._debug_json_enabled or self._debug_json_writer is None:
            return

        try:
            written_path = self._debug_json_writer.write_json(label=label, payload=payload)
        except (OSError, TypeError, ValueError) as err:
            LOGGER.warning(
                "Failed to write Structured LLM debug payload",
                extra={
                    "component": self.__class__.__name__,
                    "model": self._model,
                    "debug_label": label,
                },
            )
            LOGGER.debug("Structured LLM debug payload write error: %s", err)
            return

        LOGGER.debug(
            "Structured LLM debug payload written: %s",
            written_path,
            extra={
                "component": self.__class__.__name__,
                "model": self._model,
                "debug_label": label,
            },
        )
