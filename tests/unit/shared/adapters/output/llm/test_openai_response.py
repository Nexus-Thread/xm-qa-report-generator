"""Unit tests for shared OpenAI response parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from shared.adapters.output.llm.openai_adapter.response import (
    OpenAIResponseError,
    OpenAIResponseUsage,
    extract_message_content,
    extract_usage,
)


@dataclass(frozen=True)
class _Message:
    content: object | None


@dataclass(frozen=True)
class _Choice:
    message: _Message | None


@dataclass(frozen=True)
class _Usage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class _Response:
    choices: list[_Choice] | None = None
    usage: _Usage | None = None


def test_extract_message_content_returns_first_choice_content() -> None:
    """Response helper returns content from first choice message."""
    response = _Response(choices=[_Choice(message=_Message(content="ok"))])

    assert extract_message_content(response) == "ok"


def test_extract_message_content_raises_when_choices_are_missing() -> None:
    """Response helper raises a domain-specific error for missing choices."""
    response = _Response(choices=[])

    with pytest.raises(OpenAIResponseError, match="choices"):
        extract_message_content(response)


def test_extract_message_content_raises_when_message_is_missing() -> None:
    """Response helper raises when first choice has no message."""
    response = _Response(choices=[_Choice(message=None)])

    with pytest.raises(OpenAIResponseError, match="message"):
        extract_message_content(response)


def test_extract_message_content_raises_when_content_is_missing() -> None:
    """Response helper raises when message content is missing."""
    response = _Response(choices=[_Choice(message=_Message(content=None))])

    with pytest.raises(OpenAIResponseError, match="content"):
        extract_message_content(response)


def test_extract_message_content_supports_structured_list_with_string_parts() -> None:
    """Response helper joins text from string parts."""
    response = _Response(choices=[_Choice(message=_Message(content=["hello", " ", "world"]))])

    assert extract_message_content(response) == "hello world"


def test_extract_message_content_supports_structured_list_with_dict_text_parts() -> None:
    """Response helper joins text from dict-based parts."""
    response = _Response(
        choices=[
            _Choice(
                message=_Message(
                    content=[
                        {"type": "output_text", "text": "hello"},
                        {"type": "output_text", "text": " world"},
                    ]
                )
            )
        ]
    )

    assert extract_message_content(response) == "hello world"


def test_extract_message_content_supports_structured_list_with_nested_text_value() -> None:
    """Response helper extracts text from object parts with nested value."""
    response = _Response(
        choices=[
            _Choice(
                message=_Message(
                    content=[
                        SimpleNamespace(text=SimpleNamespace(value="hello")),
                        SimpleNamespace(text=SimpleNamespace(value=" world")),
                    ]
                )
            )
        ]
    )

    assert extract_message_content(response) == "hello world"


def test_extract_message_content_raises_when_structured_content_has_no_text() -> None:
    """Response helper raises when structured parts do not include text."""
    response = _Response(
        choices=[
            _Choice(
                message=_Message(
                    content=[
                        {"type": "output_image", "image_url": "https://example.invalid"},
                    ]
                )
            )
        ]
    )

    with pytest.raises(OpenAIResponseError, match="supported text shape"):
        extract_message_content(response)


def test_extract_usage_returns_none_when_usage_missing() -> None:
    """Response helper returns None when token usage is absent."""
    response = _Response(usage=None)

    assert extract_usage(response) is None


def test_extract_usage_returns_usage_dataclass() -> None:
    """Response helper maps usage fields into stable dataclass shape."""
    response = _Response(usage=_Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15))

    assert extract_usage(response) == OpenAIResponseUsage(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
    )
