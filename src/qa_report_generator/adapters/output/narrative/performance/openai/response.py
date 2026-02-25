"""OpenAI response parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass


class OpenAIResponseError(ValueError):
    """Raised when the OpenAI response shape is invalid."""


@dataclass(frozen=True)
class OpenAIResponseUsage:
    """Token usage metadata extracted from an OpenAI response."""

    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


def extract_message_content(response: object) -> str:
    """Extract content from the first model response choice."""
    choices = getattr(response, "choices", None)
    if not choices:
        msg = "LLM response did not include choices"
        raise OpenAIResponseError(msg)

    message = getattr(choices[0], "message", None)
    if message is None:
        msg = "LLM response did not include a message"
        raise OpenAIResponseError(msg)

    content = getattr(message, "content", None)
    if content is None:
        msg = "LLM response did not include content"
        raise OpenAIResponseError(msg)

    return content


def extract_usage(response: object) -> OpenAIResponseUsage | None:
    """Extract token usage metadata from a model response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return None

    return OpenAIResponseUsage(
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
    )
