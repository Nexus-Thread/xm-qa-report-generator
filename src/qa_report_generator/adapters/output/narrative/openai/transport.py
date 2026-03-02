"""OpenAI SDK transport wrapper."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Protocol, cast

from openai import APIError

from .constants import DEFAULT_BACKOFF_FACTOR, DEFAULT_MAX_RETRIES

if TYPE_CHECKING:
    from collections.abc import Callable

LOGGER = logging.getLogger(__name__)


class _ChatCompletionsProtocol(Protocol):
    """Private protocol for the SDK completions namespace."""

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        response_format: dict[str, str] | None = None,
    ) -> object:
        """Create a completion response from the SDK."""


class _ChatNamespaceProtocol(Protocol):
    """Private protocol for the SDK chat namespace."""

    @property
    def completions(self) -> _ChatCompletionsProtocol:
        """Return the completions API namespace."""


class _OpenAISDKClientProtocol(Protocol):
    """Private protocol for minimal OpenAI SDK client shape."""

    @property
    def chat(self) -> _ChatNamespaceProtocol:
        """Return the chat API namespace."""


class OpenAIClient:
    """Thin transport wrapper around the OpenAI SDK client."""

    def __init__(
        self,
        sdk_client: object,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Store the OpenAI SDK client."""
        if max_retries < 0:
            msg = "max_retries must be greater than or equal to 0"
            raise ValueError(msg)
        if backoff_factor < 1.0:
            msg = "backoff_factor must be greater than or equal to 1.0"
            raise ValueError(msg)

        self._sdk_client = cast("_OpenAISDKClientProtocol", sdk_client)
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._sleep = sleep

    def create_json_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
    ) -> object:
        """Create a JSON-formatted chat completion."""
        return self._create_completion(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
        )

    def create_chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
    ) -> object:
        """Create a plain chat completion without enforced response format."""
        return self._create_completion(
            model=model,
            messages=messages,
            response_format=None,
        )

    def _create_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, str] | None,
    ) -> object:
        """Invoke the SDK chat completions API with optional JSON format and retry logic."""
        total_attempts = self._max_retries + 1
        for attempt in range(1, total_attempts + 1):
            try:
                return self._chat_completions_create(model, messages, response_format=response_format)
            except APIError:
                if attempt >= total_attempts:
                    LOGGER.exception(
                        "OpenAI completion failed after retries",
                        extra={
                            "component": self.__class__.__name__,
                            "model": model,
                            "max_retries": self._max_retries,
                        },
                    )
                    raise
                delay = self._backoff_factor**attempt
                LOGGER.warning(
                    "OpenAI completion failed, retrying",
                    extra={
                        "component": self.__class__.__name__,
                        "model": model,
                        "attempt": attempt,
                        "max_retries": self._max_retries,
                        "retry_delay_seconds": delay,
                    },
                )
                self._sleep(delay)

        message = "Unexpected transport retry loop termination"
        raise RuntimeError(message)

    def _chat_completions_create(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        response_format: dict[str, str] | None,
    ) -> object:
        return self._sdk_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
            response_format=response_format,
        )
