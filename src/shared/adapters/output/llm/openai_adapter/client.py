"""OpenAI client construction helpers."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from openai import OpenAI

from .transport import DEFAULT_BACKOFF_FACTOR, DEFAULT_MAX_RETRIES, OpenAIClient

DEFAULT_VERIFY_SSL = True
DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class OpenAIClientSettings:
    """Configuration for creating an OpenAI transport client."""

    base_url: str
    api_key: str
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
    verify_ssl: bool = DEFAULT_VERIFY_SSL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def build_client(settings: OpenAIClientSettings) -> OpenAIClient:
    """Build an OpenAI transport client from explicit settings."""
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
        backoff_factor=settings.backoff_factor,
    )
