"""Unit tests for OpenAI client construction helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

import pytest

from qa_report_generator_performance.adapters.output.narrative.openai_adapter import OpenAIClient, OpenAIClientSettings, build_client


class _TimeoutLike(Protocol):
    """Protocol for timeout objects used by the builder tests."""

    @property
    def connect(self) -> float | None:
        """Return configured connect timeout."""


@dataclass(frozen=True)
class _HttpClientCall:
    verify: bool
    timeout: _TimeoutLike


@dataclass(frozen=True)
class _StubHttpClient:
    verify: bool
    timeout: _TimeoutLike


@dataclass(frozen=True)
class _OpenAiCall:
    base_url: str
    api_key: str
    http_client: _StubHttpClient


class _HttpClientFactoryStub:
    """Stub HTTP client constructor for builder tests."""

    def __init__(self) -> None:
        self.calls: list[_HttpClientCall] = []

    def __call__(self, *, verify: bool, timeout: object) -> _StubHttpClient:
        timeout_like = cast("_TimeoutLike", timeout)
        self.calls.append(_HttpClientCall(verify=verify, timeout=timeout_like))
        return _StubHttpClient(verify=verify, timeout=timeout_like)


class _OpenAiFactoryStub:
    """Stub OpenAI SDK constructor for builder tests."""

    def __init__(self) -> None:
        self.calls: list[_OpenAiCall] = []

    def __call__(self, *, base_url: str, api_key: str, http_client: _StubHttpClient) -> object:
        self.calls.append(
            _OpenAiCall(
                base_url=base_url,
                api_key=api_key,
                http_client=http_client,
            )
        )
        return object()


def test_build_client_creates_transport_with_explicit_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Client builder wires timeout, SSL, and retry settings into the transport."""
    http_client_factory = _HttpClientFactoryStub()
    openai_factory = _OpenAiFactoryStub()
    monkeypatch.setattr(
        "qa_report_generator_performance.adapters.output.narrative.openai_adapter.client.httpx.Client",
        http_client_factory,
    )
    monkeypatch.setattr(
        "qa_report_generator_performance.adapters.output.narrative.openai_adapter.client.OpenAI",
        openai_factory,
    )

    client = build_client(
        OpenAIClientSettings(
            base_url="https://example.invalid/v1",
            api_key="test-key",
            max_retries=5,
            backoff_factor=4.0,
            verify_ssl=False,
            timeout_seconds=12.5,
        )
    )

    assert isinstance(client, OpenAIClient)
    assert len(http_client_factory.calls) == 1
    http_client_call = http_client_factory.calls[0]
    assert http_client_call.verify is False
    assert http_client_call.timeout.connect == pytest.approx(12.5, rel=0, abs=0)
    assert len(openai_factory.calls) == 1
    call = openai_factory.calls[0]
    assert call.base_url == "https://example.invalid/v1"
    assert call.api_key == "test-key"
    assert call.http_client.verify is False
    assert call.http_client.timeout.connect == pytest.approx(12.5, rel=0, abs=0)


def test_build_client_uses_default_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Client builder applies package defaults when optional settings are omitted."""
    http_client_factory = _HttpClientFactoryStub()
    openai_factory = _OpenAiFactoryStub()
    monkeypatch.setattr(
        "qa_report_generator_performance.adapters.output.narrative.openai_adapter.client.httpx.Client",
        http_client_factory,
    )
    monkeypatch.setattr(
        "qa_report_generator_performance.adapters.output.narrative.openai_adapter.client.OpenAI",
        openai_factory,
    )

    client = build_client(
        OpenAIClientSettings(
            base_url="https://example.invalid/v1",
            api_key="test-key",
        )
    )

    assert isinstance(client, OpenAIClient)
    assert len(http_client_factory.calls) == 1
    http_client_call = http_client_factory.calls[0]
    assert http_client_call.verify is True
    assert http_client_call.timeout.connect == pytest.approx(30.0, rel=0, abs=0)
    assert len(openai_factory.calls) == 1
    call = openai_factory.calls[0]
    assert call.http_client.verify is True
    assert call.http_client.timeout.connect == pytest.approx(30.0, rel=0, abs=0)
