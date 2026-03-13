"""Structured JSON completion adapter using OpenAI transport."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from .logging_utils import truncate_for_log
from .response_parser import extract_structured_content, parse_json_object

if TYPE_CHECKING:
    from qa_report_generator_performance.adapters.output.narrative.openai_adapter import OpenAIClientProtocol
    from qa_report_generator_performance.application.ports.output import JsonWriterPort

LOGGER = logging.getLogger(__name__)


class OpenAIStructuredLlmAdapter:
    """Generate deterministic JSON objects through OpenAI chat completions."""

    def __init__(
        self,
        *,
        client: OpenAIClientProtocol,
        model: str,
        debug_json_writer: JsonWriterPort | None = None,
        debug_json_enabled: bool = False,
    ) -> None:
        """Store transport client and runtime configuration."""
        self._client = client
        self._model = model
        self._debug_json_writer = debug_json_writer
        self._debug_json_enabled = debug_json_enabled

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return parsed JSON payload from model response."""
        messages = self._build_messages(system_prompt=system_prompt, user_prompt=user_prompt)
        request_payload = self._build_request_payload(messages=messages)
        self._log_json_stage(
            label="request_payload",
            payload=request_payload,
            message="Structured LLM request payload",
        )

        response = self._client.create_json_completion(model=self._model, messages=messages)
        content = extract_structured_content(response)
        self._log_text_stage(
            label="response_content",
            content=content,
            message="Structured LLM response content",
        )

        payload = parse_json_object(content)
        self._log_json_stage(
            label="parsed_payload",
            payload=payload,
            message="Structured LLM parsed JSON payload",
            extra={"payload_keys": list(payload.keys())},
        )
        return payload

    def _build_messages(self, *, system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
        """Build chat messages for the structured completion request."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_request_payload(self, *, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Build the debug/log payload for a completion request."""
        return {"model": self._model, "messages": messages}

    def _log_json_stage(
        self,
        *,
        label: str,
        payload: Any,
        message: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Write and log one JSON-serializable stage payload."""
        self._write_debug_payload(label=label, payload=payload)
        self._log_payload_preview(
            message=message,
            serialized_payload=json.dumps(payload, ensure_ascii=False),
            extra=extra,
        )

    def _log_text_stage(
        self,
        *,
        label: str,
        content: str,
        message: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Write and log one text stage payload."""
        self._write_debug_payload(label=label, payload={"content": content})
        self._log_payload_preview(message=message, serialized_payload=content, extra=extra)

    def _log_payload_preview(
        self,
        *,
        message: str,
        serialized_payload: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log a truncated preview and shared metadata for one payload."""
        payload_preview, payload_truncated = truncate_for_log(serialized_payload)
        log_extra: dict[str, Any] = {
            "component": self.__class__.__name__,
            "model": self._model,
            "payload_length": len(serialized_payload),
            "payload_truncated": payload_truncated,
        }
        if extra is not None:
            log_extra.update(extra)

        LOGGER.debug("%s: %s", message, payload_preview, extra=log_extra)

    def _write_debug_payload(self, *, label: str, payload: Any) -> None:
        """Write debug payload if JSON debug output is enabled."""
        if not self._debug_json_enabled or self._debug_json_writer is None:
            return

        try:
            written_path = self._debug_json_writer.write_json(label=label, payload=payload)
        except (OSError, TypeError, ValueError) as err:
            LOGGER.warning(
                "Failed to write Structured LLM debug payload",
                exc_info=err,
                extra={
                    "component": self.__class__.__name__,
                    "model": self._model,
                    "debug_label": label,
                },
            )
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
