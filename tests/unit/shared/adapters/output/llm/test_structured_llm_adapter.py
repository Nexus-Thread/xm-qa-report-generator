"""Unit tests for the shared structured LLM adapter."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest

from shared.adapters.output.llm.structured_llm_adapter import (
    OpenAIStructuredLlmAdapter,
    StructuredLlmInvalidJsonError,
    StructuredLlmResponseError,
)

LOGGER_NAME = "shared.adapters.output.llm.structured_llm_adapter.adapter"


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


class _StubDebugJsonWriter:
    """Stub debug JSON writer for structured adapter tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def write_json(self, *, label: str, payload: object) -> Path:
        self.calls.append((label, payload))
        return Path(f"debug/{label}.json")


class _FailingDebugJsonWriter:
    """Stub debug JSON writer that fails for resilience testing."""

    def __init__(self, exception: Exception) -> None:
        self._exception = exception
        self.calls: list[tuple[str, object]] = []

    def write_json(self, *, label: str, payload: object) -> Path:
        self.calls.append((label, payload))
        raise self._exception


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
    """Structured adapter raises a shared invalid-JSON error."""
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content="{not-json"))])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    with pytest.raises(StructuredLlmInvalidJsonError, match="invalid JSON payload"):
        adapter.complete_json(system_prompt="system", user_prompt="user")


def test_complete_json_raises_when_payload_is_not_object() -> None:
    """Structured adapter requires a top-level JSON object payload."""
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content="[]"))])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    with pytest.raises(StructuredLlmInvalidJsonError, match="JSON object"):
        adapter.complete_json(system_prompt="system", user_prompt="user")


def test_complete_json_raises_when_message_content_missing() -> None:
    """Structured adapter raises a shared response-shape error."""
    client = _StubClient([_Response(choices=[_Choice(message=None)])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    with pytest.raises(StructuredLlmResponseError, match="missing content"):
        adapter.complete_json(system_prompt="system", user_prompt="user")


def test_complete_json_logs_request_response_and_payload(caplog: pytest.LogCaptureFixture) -> None:
    """Structured adapter emits debug logs for request and response lifecycle."""
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content='{"ok": true}'))])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        payload = adapter.complete_json(system_prompt="system", user_prompt="user")

    assert payload == {"ok": True}

    request_record = next(record for record in caplog.records if record.getMessage().startswith("Structured LLM request payload"))
    response_record = next(record for record in caplog.records if record.getMessage().startswith("Structured LLM response content"))
    parsed_record = next(record for record in caplog.records if record.getMessage().startswith("Structured LLM parsed JSON payload"))
    request_record_any = cast("Any", request_record)
    response_record_any = cast("Any", response_record)
    parsed_record_any = cast("Any", parsed_record)

    assert request_record_any.model == "gpt-test"
    assert request_record_any.payload_truncated is False
    assert response_record_any.payload_truncated is False
    assert parsed_record_any.payload_truncated is False
    assert parsed_record_any.payload_keys == ["ok"]


def test_complete_json_truncates_large_request_and_response_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Structured adapter truncates oversized payloads in debug logs."""
    long_text = "x" * 2_100_000
    content = json.dumps({"summary": long_text})
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content=content))])])
    adapter = OpenAIStructuredLlmAdapter(client=client, model="gpt-test")

    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        adapter.complete_json(system_prompt="system", user_prompt=long_text)

    request_record = next(record for record in caplog.records if record.getMessage().startswith("Structured LLM request payload"))
    response_record = next(record for record in caplog.records if record.getMessage().startswith("Structured LLM response content"))
    parsed_record = next(record for record in caplog.records if record.getMessage().startswith("Structured LLM parsed JSON payload"))
    request_record_any = cast("Any", request_record)
    response_record_any = cast("Any", response_record)
    parsed_record_any = cast("Any", parsed_record)

    assert request_record_any.payload_truncated is True
    assert response_record_any.payload_truncated is True
    assert parsed_record_any.payload_truncated is True
    assert "...[truncated]" in request_record.getMessage()
    assert "...[truncated]" in response_record.getMessage()
    assert "...[truncated]" in parsed_record.getMessage()


def test_complete_json_writes_debug_files_when_enabled() -> None:
    """Structured adapter writes request/response/parsed payloads when debug enabled."""
    debug_writer = _StubDebugJsonWriter()
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content='{"ok": true}'))])])
    adapter = OpenAIStructuredLlmAdapter(
        client=client,
        model="gpt-test",
        debug_json_writer=debug_writer,
        debug_json_enabled=True,
    )

    payload = adapter.complete_json(system_prompt="system", user_prompt="user")

    assert payload == {"ok": True}
    assert [label for label, _ in debug_writer.calls] == [
        "request_payload",
        "response_content",
        "parsed_payload",
    ]


def test_complete_json_skips_debug_files_when_disabled() -> None:
    """Structured adapter does not write debug files when debug is disabled."""
    debug_writer = _StubDebugJsonWriter()
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content='{"ok": true}'))])])
    adapter = OpenAIStructuredLlmAdapter(
        client=client,
        model="gpt-test",
        debug_json_writer=debug_writer,
        debug_json_enabled=False,
    )

    payload = adapter.complete_json(system_prompt="system", user_prompt="user")

    assert payload == {"ok": True}
    assert debug_writer.calls == []


def test_complete_json_continues_when_debug_write_fails(caplog: pytest.LogCaptureFixture) -> None:
    """Structured adapter continues when optional debug payload persistence fails."""
    debug_writer = _FailingDebugJsonWriter(OSError("disk full"))
    client = _StubClient([_Response(choices=[_Choice(message=_Message(content='{"ok": true}'))])])
    adapter = OpenAIStructuredLlmAdapter(
        client=client,
        model="gpt-test",
        debug_json_writer=debug_writer,
        debug_json_enabled=True,
    )

    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        payload = adapter.complete_json(system_prompt="system", user_prompt="user")

    assert payload == {"ok": True}
    assert [label for label, _ in debug_writer.calls] == [
        "request_payload",
        "response_content",
        "parsed_payload",
    ]
    warning_messages = [record.getMessage() for record in caplog.records]
    assert warning_messages == [
        "Failed to write Structured LLM debug payload",
        "Failed to write Structured LLM debug payload",
        "Failed to write Structured LLM debug payload",
    ]
    assert all(record.exc_info is not None for record in caplog.records)
