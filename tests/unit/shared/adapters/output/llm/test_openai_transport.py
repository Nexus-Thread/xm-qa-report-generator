"""Unit tests for shared OpenAI transport retry behavior."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, cast

import httpx
import pytest
from openai import APIError

from shared.adapters.output.llm.openai_adapter.transport import OpenAIClient

LOGGER_NAME = "shared.adapters.output.llm.openai_adapter.transport"


@dataclass(frozen=True)
class _CreateCall:
    model: str
    messages: list[dict[str, str]]
    temperature: float
    response_format: dict[str, str] | None


class _StubCompletions:
    """Stub chat completions endpoint for deterministic transport tests."""

    def __init__(self, outcomes: list[object]) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[_CreateCall] = []

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        response_format: dict[str, str] | None = None,
    ) -> object:
        self.calls.append(
            _CreateCall(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format=response_format,
            )
        )
        outcome = self._outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


@dataclass
class _StubChatNamespace:
    completions: _StubCompletions


@dataclass
class _StubSdkClient:
    chat: _StubChatNamespace


def _build_client(*, outcomes: list[object], max_retries: int, backoff_factor: float, sleeps: list[float]) -> tuple[OpenAIClient, _StubCompletions]:
    completions = _StubCompletions(outcomes)
    sdk_client = _StubSdkClient(chat=_StubChatNamespace(completions=completions))
    client = OpenAIClient(
        sdk_client=sdk_client,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        sleep=sleeps.append,
    )
    return client, completions


def _api_error() -> APIError:
    request = httpx.Request("POST", "https://example.invalid/v1/chat/completions")
    return APIError("boom", request=request, body=None)


def test_create_json_completion_passes_json_response_format() -> None:
    """Transport passes OpenAI JSON mode options to the SDK."""
    sleeps: list[float] = []
    expected_response = object()
    client, completions = _build_client(
        outcomes=[expected_response],
        max_retries=0,
        backoff_factor=2.0,
        sleeps=sleeps,
    )

    response = client.create_json_completion(model="gpt-test", messages=[{"role": "user", "content": "hello"}])

    assert response is expected_response
    assert len(completions.calls) == 1
    assert completions.calls[0].temperature == 0
    assert completions.calls[0].response_format == {"type": "json_object"}
    assert sleeps == []


def test_create_chat_completion_omits_response_format() -> None:
    """Transport sends plain chat completion options when JSON mode is not requested."""
    sleeps: list[float] = []
    expected_response = object()
    client, completions = _build_client(
        outcomes=[expected_response],
        max_retries=0,
        backoff_factor=2.0,
        sleeps=sleeps,
    )

    response = client.create_chat_completion(model="gpt-test", messages=[{"role": "user", "content": "hello"}])

    assert response is expected_response
    assert len(completions.calls) == 1
    assert completions.calls[0].temperature == 0
    assert completions.calls[0].response_format is None
    assert sleeps == []


def test_create_chat_completion_retries_and_then_succeeds() -> None:
    """Transport retries API errors up to the configured retry count."""
    sleeps: list[float] = []
    expected_response = object()
    client, completions = _build_client(
        outcomes=[_api_error(), expected_response],
        max_retries=2,
        backoff_factor=3.0,
        sleeps=sleeps,
    )

    response = client.create_chat_completion(model="gpt-test", messages=[{"role": "user", "content": "hello"}])

    assert response is expected_response
    assert len(completions.calls) == 2
    assert sleeps == [3.0]


def test_create_chat_completion_logs_retry_metadata(caplog: pytest.LogCaptureFixture) -> None:
    """Transport logs actionable retry metadata for transient API failures."""
    sleeps: list[float] = []
    expected_response = object()
    client, _ = _build_client(
        outcomes=[_api_error(), expected_response],
        max_retries=2,
        backoff_factor=3.0,
        sleeps=sleeps,
    )

    with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
        response = client.create_chat_completion(model="gpt-test", messages=[{"role": "user", "content": "hello"}])

    assert response is expected_response
    warning_record = caplog.records[0]
    assert warning_record.getMessage() == "OpenAI completion attempt failed; retrying"
    warning_record_any = cast("Any", warning_record)
    assert warning_record_any.attempt == 1
    assert warning_record_any.attempts_remaining == 2
    assert warning_record_any.total_attempts == 3
    assert warning_record_any.retry_delay_seconds == 3.0


def test_create_chat_completion_with_zero_retries_still_attempts_once() -> None:
    """Transport performs one initial request when retries are configured to zero."""
    sleeps: list[float] = []
    client, completions = _build_client(
        outcomes=[_api_error()],
        max_retries=0,
        backoff_factor=2.0,
        sleeps=sleeps,
    )

    with pytest.raises(APIError):
        client.create_chat_completion(model="gpt-test", messages=[{"role": "user", "content": "hello"}])

    assert len(completions.calls) == 1
    assert sleeps == []


def test_create_chat_completion_raises_after_exhausting_retries() -> None:
    """Transport raises APIError after all retry attempts are exhausted."""
    sleeps: list[float] = []
    client, completions = _build_client(
        outcomes=[_api_error(), _api_error(), _api_error()],
        max_retries=2,
        backoff_factor=2.0,
        sleeps=sleeps,
    )

    with pytest.raises(APIError):
        client.create_chat_completion(model="gpt-test", messages=[{"role": "user", "content": "hello"}])

    assert len(completions.calls) == 3
    assert sleeps == [2.0, 4.0]


def test_create_chat_completion_logs_final_exception_once(caplog: pytest.LogCaptureFixture) -> None:
    """Transport logs one final exception with retry context when exhausted."""
    sleeps: list[float] = []
    client, _ = _build_client(
        outcomes=[_api_error(), _api_error()],
        max_retries=1,
        backoff_factor=2.0,
        sleeps=sleeps,
    )

    with caplog.at_level(logging.ERROR, logger=LOGGER_NAME), pytest.raises(APIError):
        client.create_chat_completion(model="gpt-test", messages=[{"role": "user", "content": "hello"}])

    exception_record = next(record for record in caplog.records if record.levelno == logging.ERROR)
    assert exception_record.getMessage() == "OpenAI completion failed after exhausting retries"
    exception_record_any = cast("Any", exception_record)
    assert exception_record_any.attempt == 2
    assert exception_record_any.total_attempts == 2
    assert exception_record.exc_info is not None


def test_init_rejects_invalid_retry_configuration() -> None:
    """Transport validates retry and backoff constructor arguments."""
    with pytest.raises(ValueError, match="max_retries"):
        OpenAIClient(sdk_client=object(), max_retries=-1)

    with pytest.raises(ValueError, match="backoff_factor"):
        OpenAIClient(sdk_client=object(), backoff_factor=0.5)
