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

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        extracted_parts = [_extract_content_part_text(part) for part in content]
        extracted_text = "".join(part for part in extracted_parts if part is not None)
        if extracted_text:
            return extracted_text

    msg = "LLM response content is not a supported text shape"
    raise OpenAIResponseError(msg)


def _extract_content_part_text(part: object) -> str | None:
    """Extract text from a structured content part."""
    if isinstance(part, str):
        return part

    if isinstance(part, dict):
        text = part.get("text")
        return text if isinstance(text, str) else None

    text = getattr(part, "text", None)
    if isinstance(text, str):
        return text

    nested_text = _extract_nested_text_field(part)
    if isinstance(nested_text, str):
        return nested_text

    return None


def _extract_nested_text_field(part: object) -> object:
    """Return nested text value when content part exposes rich text objects."""
    text = getattr(part, "text", None)
    if text is None:
        return None
    return getattr(text, "value", None)


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
