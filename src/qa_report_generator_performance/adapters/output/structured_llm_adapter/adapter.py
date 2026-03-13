"""Application adapter that translates shared structured LLM errors."""

from __future__ import annotations

from typing import Any, Protocol

from qa_report_generator_performance.application.exceptions import ExtractionVerificationError
from shared.adapters.output.llm import OpenAIResponseUsage, StructuredLlmError, StructuredLlmJsonCompletionResult


class StructuredJsonCompletionProtocol(Protocol):
    """Protocol for shared structured JSON completion adapters."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a JSON object parsed from an LLM response."""

    def complete_json_with_metadata(self, *, system_prompt: str, user_prompt: str) -> StructuredLlmJsonCompletionResult:
        """Return a structured JSON completion plus usage metadata."""


class LlmUsageRecorderProtocol(Protocol):
    """Protocol for recording usage emitted by the shared structured adapter."""

    def record_usage(self, *, usage: OpenAIResponseUsage | None) -> None:
        """Record usage from one structured LLM call."""


class StructuredLlmPortAdapter:
    """Translate shared structured LLM errors into application errors."""

    def __init__(self, *, adapter: StructuredJsonCompletionProtocol, usage_tracker: LlmUsageRecorderProtocol | None = None) -> None:
        """Store the shared structured completion adapter."""
        self._adapter = adapter
        self._usage_tracker = usage_tracker

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Delegate completion and map shared failures into application failures."""
        try:
            completion_result = self._adapter.complete_json_with_metadata(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except StructuredLlmError as err:
            raise ExtractionVerificationError(err.message, suggestion=err.suggestion) from err

        if self._usage_tracker is not None:
            self._usage_tracker.record_usage(usage=completion_result.usage)
        return completion_result.payload
