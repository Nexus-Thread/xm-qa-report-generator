"""Application adapter that translates shared structured LLM errors."""

from __future__ import annotations

from typing import Any, Protocol

from qa_report_generator_performance.application.exceptions import ExtractionVerificationError
from shared.adapters.output.llm import StructuredLlmError


class StructuredJsonCompletionProtocol(Protocol):
    """Protocol for shared structured JSON completion adapters."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a JSON object parsed from an LLM response."""


class StructuredLlmPortAdapter:
    """Translate shared structured LLM errors into application errors."""

    def __init__(self, *, adapter: StructuredJsonCompletionProtocol) -> None:
        """Store the shared structured completion adapter."""
        self._adapter = adapter

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Delegate completion and map shared failures into application failures."""
        try:
            return self._adapter.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
        except StructuredLlmError as err:
            raise ExtractionVerificationError(err.message, suggestion=err.suggestion) from err
