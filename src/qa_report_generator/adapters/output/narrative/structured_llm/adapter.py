"""Structured JSON completion adapter using OpenAI transport."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from .logging_utils import truncate_for_log
from .response_parser import extract_structured_content, parse_json_object

if TYPE_CHECKING:
    from qa_report_generator.adapters.output.narrative.openai.protocols import OpenAIClientProtocol
    from qa_report_generator.application.ports.output import DebugJsonWriterPort

LOGGER = logging.getLogger(__name__)


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
        request_payload_preview, request_payload_truncated = truncate_for_log(request_payload_json)
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
        content = extract_structured_content(response)
        self._write_debug_payload(label="response_content", payload={"content": content})
        response_preview, response_truncated = truncate_for_log(content)
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

        payload = parse_json_object(content)

        self._write_debug_payload(label="parsed_payload", payload=payload)
        parsed_payload_json = json.dumps(payload, ensure_ascii=False)
        parsed_payload_preview, parsed_payload_truncated = truncate_for_log(parsed_payload_json)
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
