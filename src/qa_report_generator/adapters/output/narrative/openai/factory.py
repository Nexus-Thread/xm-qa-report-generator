"""Factory helpers for OpenAI transport clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx
from openai import OpenAI

from .constants import DEFAULT_BACKOFF_SECONDS, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT_SECONDS, DEFAULT_VERIFY_SSL
from .transport import OpenAIClient


class OpenAIClientSettingsProtocol(Protocol):
    """Settings required to build an OpenAI transport client."""

    @property
    def base_url(self) -> str:
        """Return OpenAI base URL."""

    @property
    def api_key(self) -> str:
        """Return OpenAI API key."""

    @property
    def max_retries(self) -> int:
        """Return maximum retry attempts."""

    @property
    def backoff_seconds(self) -> float:
        """Return base backoff duration in seconds."""

    @property
    def verify_ssl(self) -> bool:
        """Return SSL verification flag."""

    @property
    def timeout_seconds(self) -> float:
        """Return HTTP client timeout in seconds."""


@dataclass(frozen=True)
class OpenAIClientSettings:
    """Explicit settings object for OpenAI client factory calls."""

    base_url: str
    api_key: str
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS
    verify_ssl: bool = DEFAULT_VERIFY_SSL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def build_client(settings: OpenAIClientSettingsProtocol) -> OpenAIClient:
    """Create an OpenAI-compatible client from dynamic settings."""
    timeout = httpx.Timeout(settings.timeout_seconds)
    http_client = httpx.Client(
        verify=settings.verify_ssl,
        timeout=timeout,
    )
    sdk_client = OpenAI(
        base_url=settings.base_url,
        api_key=settings.api_key,
        http_client=http_client,
    )
    return OpenAIClient(
        sdk_client=sdk_client,
        max_retries=settings.max_retries,
        backoff_seconds=settings.backoff_seconds,
    )
