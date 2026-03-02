"""Unit tests for the structured LLM output adapter."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from qa_report_generator.adapters.output.narrative.structured_llm import OpenAIStructuredLlmAdapter
from qa_report_generator.domain.exceptions import ExtractionVerificationError


@dataclass(frozen=True)
class _Message:
    content: str | None


@dataclass(frozen=True)
class _Choice:
    message: _Message | None


@dataclass(frozen=True)
class _Response:
    choices: list[_Choice] | None


class _StubClient:
    """Stub OpenAI transport for structured adapter tests."""

    def __init__(self, responses: list[object]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[str, list[dict[str, str]]]] = []

    def create_json_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
    ) -> object:
        self.calls.append((model, messages))
        return self._responses.pop(0)

    def create_chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
    ) -> object:
        self.calls.append((model, messages))
        return self._responses.pop(0)


def test_complete_json_returns_payload_and_formats_messages() -> None:
    """Structured adapter returns parsed dict and sends expected prompts."""
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content='{"ok": true}'))])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    payload = adapter.complete_json(system_prompt="system", user_prompt="user")

    assert payload == {"ok": True}
    assert client.calls == [
        (
            "gpt-test",
            [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
        )
    ]


def test_complete_json_raises_on_invalid_json() -> None:
    """Structured adapter wraps JSON decode failures as verification errors."""
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content="{not-json"))])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    with pytest.raises(ExtractionVerificationError, match="invalid JSON payload"):
        adapter.complete_json(system_prompt="system", user_prompt="user")


def test_complete_json_raises_when_payload_is_not_object() -> None:
    """Structured adapter requires a top-level JSON object payload."""
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content="[]"))])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    with pytest.raises(ExtractionVerificationError, match="JSON object"):
        adapter.complete_json(system_prompt="system", user_prompt="user")


def test_complete_json_raises_when_message_content_missing() -> None:
    """Structured adapter maps missing response content into verification error."""
    client = _StubClient([_Response(choices=[_Choice(message=None)])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    with pytest.raises(ExtractionVerificationError, match="missing content"):
        adapter.complete_json(system_prompt="system", user_prompt="user")
