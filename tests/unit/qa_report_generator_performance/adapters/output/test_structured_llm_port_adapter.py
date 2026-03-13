"""Unit tests for the application-specific structured LLM translation adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from qa_report_generator_performance.adapters.output.structured_llm_adapter import StructuredLlmPortAdapter
from qa_report_generator_performance.application.exceptions import ExtractionVerificationError
from shared.adapters.output.llm import StructuredLlmInvalidJsonError


@dataclass(frozen=True)
class _StubSharedAdapter:
    payload: dict[str, Any]

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a deterministic payload."""
        del system_prompt, user_prompt
        return self.payload


class _FailingSharedAdapter:
    """Stub shared adapter that raises a shared structured LLM error."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Raise a reusable shared adapter error."""
        del system_prompt, user_prompt
        message = "invalid JSON payload"
        suggestion = "Inspect the shared prompts"
        raise StructuredLlmInvalidJsonError(message, suggestion=suggestion)


def test_complete_json_returns_shared_adapter_payload() -> None:
    """App translation adapter returns the delegated payload unchanged."""
    adapter = StructuredLlmPortAdapter(adapter=_StubSharedAdapter(payload={"ok": True}))

    assert adapter.complete_json(system_prompt="system", user_prompt="user") == {"ok": True}


def test_complete_json_translates_shared_error_to_application_error() -> None:
    """App translation adapter maps shared errors into application exceptions."""
    adapter = StructuredLlmPortAdapter(adapter=_FailingSharedAdapter())

    with pytest.raises(ExtractionVerificationError, match="invalid JSON payload") as exc_info:
        adapter.complete_json(system_prompt="system", user_prompt="user")

    assert exc_info.value.suggestion == "Inspect the shared prompts"
