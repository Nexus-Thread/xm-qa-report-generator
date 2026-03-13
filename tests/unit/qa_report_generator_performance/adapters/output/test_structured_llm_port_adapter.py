"""Unit tests for the application-specific structured LLM translation adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from qa_report_generator_performance.adapters.output.structured_llm_adapter import StructuredLlmPortAdapter
from qa_report_generator_performance.application.exceptions import ExtractionVerificationError
from shared.adapters.output.llm import OpenAIResponseUsage, StructuredLlmInvalidJsonError, StructuredLlmJsonCompletionResult


@dataclass(frozen=True)
class _StubSharedAdapter:
    payload: dict[str, Any]

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a deterministic payload."""
        del system_prompt, user_prompt
        return self.payload

    def complete_json_with_metadata(self, *, system_prompt: str, user_prompt: str) -> StructuredLlmJsonCompletionResult:
        """Return payload and synthetic usage metadata."""
        del system_prompt, user_prompt
        return StructuredLlmJsonCompletionResult(
            payload=self.payload,
            usage=OpenAIResponseUsage(prompt_tokens=12, completion_tokens=3, total_tokens=15),
        )


class _FailingSharedAdapter:
    """Stub shared adapter that raises a shared structured LLM error."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Raise a reusable shared adapter error."""
        del system_prompt, user_prompt
        message = "invalid JSON payload"
        suggestion = "Inspect the shared prompts"
        raise StructuredLlmInvalidJsonError(message, suggestion=suggestion)

    def complete_json_with_metadata(self, *, system_prompt: str, user_prompt: str) -> StructuredLlmJsonCompletionResult:
        """Raise the same shared error for metadata callers."""
        del system_prompt, user_prompt
        message = "invalid JSON payload"
        suggestion = "Inspect the shared prompts"
        raise StructuredLlmInvalidJsonError(message, suggestion=suggestion)


class _SpyUsageTracker:
    """Spy usage tracker for port adapter tests."""

    def __init__(self) -> None:
        """Initialize recorded usages."""
        self.calls: list[OpenAIResponseUsage | None] = []

    def record_usage(self, *, usage: OpenAIResponseUsage | None) -> None:
        """Record one delegated usage snapshot."""
        self.calls.append(usage)


def test_complete_json_returns_shared_adapter_payload() -> None:
    """App translation adapter returns the delegated payload unchanged."""
    adapter = StructuredLlmPortAdapter(adapter=_StubSharedAdapter(payload={"ok": True}))

    assert adapter.complete_json(system_prompt="system", user_prompt="user") == {"ok": True}


def test_complete_json_records_usage_when_tracker_configured() -> None:
    """App translation adapter forwards shared usage into the configured tracker."""
    usage_tracker = _SpyUsageTracker()
    adapter = StructuredLlmPortAdapter(adapter=_StubSharedAdapter(payload={"ok": True}), usage_tracker=usage_tracker)

    payload = adapter.complete_json(system_prompt="system", user_prompt="user")

    assert payload == {"ok": True}
    assert usage_tracker.calls == [
        OpenAIResponseUsage(prompt_tokens=12, completion_tokens=3, total_tokens=15),
    ]


def test_complete_json_translates_shared_error_to_application_error() -> None:
    """App translation adapter maps shared errors into application exceptions."""
    adapter = StructuredLlmPortAdapter(adapter=_FailingSharedAdapter())

    with pytest.raises(ExtractionVerificationError, match="invalid JSON payload") as exc_info:
        adapter.complete_json(system_prompt="system", user_prompt="user")

    assert exc_info.value.suggestion == "Inspect the shared prompts"
