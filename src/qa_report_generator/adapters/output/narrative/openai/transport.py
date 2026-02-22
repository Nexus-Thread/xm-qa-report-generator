"""OpenAI SDK transport wrapper."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Protocol, cast

from openai import APIConnectionError, APIError, APITimeoutError, AuthenticationError, RateLimitError

from qa_report_generator.adapters.output.narrative.openai.constants import DEFAULT_BACKOFF_SECONDS, DEFAULT_MAX_RETRIES
from qa_report_generator.domain.exceptions import GenerationError, LLMConnectionError, LLMTimeoutError

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
        temperature: float | None = None,
        reasoning_effort: str | None = None,
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
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Store the OpenAI SDK client."""
        self._sdk_client = cast("_OpenAISDKClientProtocol", sdk_client)
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._sleep = sleep

    def create_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        reasoning_effort: str | None,
    ) -> object:
        """Create a chat completion."""
        for attempt in range(self._max_retries + 1):
            try:
                return self._chat_completions_create(model, messages, temperature, reasoning_effort)
            except APITimeoutError as err:
                if attempt >= self._max_retries:
                    msg = f"LLM request timed out after {self._max_retries + 1} attempts (model: {model})"
                    raise LLMTimeoutError(msg) from err
                self._sleep(self._backoff_seconds * (2**attempt))
            except APIConnectionError as err:
                if attempt >= self._max_retries:
                    msg = f"Cannot connect to LLM service after {self._max_retries + 1} attempts"
                    raise LLMConnectionError(msg) from err
                self._sleep(self._backoff_seconds * (2**attempt))
            except (RateLimitError, AuthenticationError, APIError) as err:
                if attempt >= self._max_retries:
                    msg = "LLM request failed after retries"
                    raise GenerationError(msg) from err
                self._sleep(self._backoff_seconds * (2**attempt))

        msg = "Unreachable retry state"
        raise RuntimeError(msg)

    def _chat_completions_create(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float | None,
        reasoning_effort: str | None,
    ) -> object:
        LOGGER.debug("OpenAI completion request", extra={"component": self.__class__.__name__, "model": model})
        if temperature is None and reasoning_effort is None:
            return self._sdk_client.chat.completions.create(
                model=model,
                messages=messages,
            )
        if reasoning_effort is None:
            return self._sdk_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
        if temperature is None:
            return self._sdk_client.chat.completions.create(
                model=model,
                messages=messages,
                reasoning_effort=reasoning_effort,
            )

        return self._sdk_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            reasoning_effort=reasoning_effort,
        )
