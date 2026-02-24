"""Unit tests for the NarrativeAdapter."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from openai import APIConnectionError, APIError, APITimeoutError, AuthenticationError, RateLimitError

from qa_report_generator.adapters.output.narrative import NarrativeAdapter, NarrativeAdapterConfig
from qa_report_generator.application.dtos import SectionPrompt
from qa_report_generator.domain.value_objects import SectionType


def _make_adapter(client: Mock, **overrides: Any) -> NarrativeAdapter:
    defaults = {"llm_model": "test-model"}
    defaults.update(overrides)
    config = NarrativeAdapterConfig(**defaults)
    return NarrativeAdapter(config, client=client)


def _make_response(content: str) -> Mock:
    message = Mock()
    message.content = content
    choice = Mock()
    choice.message = message
    response = Mock()
    response.choices = [choice]
    return response


def _make_openai_error(error_cls: type[Exception], message: str) -> Exception:
    error = error_cls.__new__(error_cls)
    Exception.__init__(error, message)
    return error


def test_generate_success(caplog: pytest.LogCaptureFixture) -> None:
    client = Mock()
    client.create_chat_completion.return_value = _make_response("hello")
    adapter = _make_adapter(client)
    adapter.tokenizer = Mock()
    adapter.tokenizer.encode.return_value = list(range(12))

    # Enable INFO logging to trigger token encoding
    with caplog.at_level("INFO"):
        result = adapter.generate(
            SectionPrompt(SectionType.EXECUTIVE_SUMMARY, "system"),
            user_prompt="user",
        )

    assert result == "hello"
    client.create_chat_completion.assert_called_once_with(
        model="test-model",
        messages=[
            {"role": "system", "content": "system"},
            {"role": "user", "content": "user"},
        ],
    )
    adapter.tokenizer.encode.assert_any_call("system")
    adapter.tokenizer.encode.assert_any_call("user")


def test_logs_token_usage_at_info(caplog: pytest.LogCaptureFixture) -> None:
    client = Mock()
    client.create_chat_completion.return_value = _make_response("ok")
    adapter = _make_adapter(client)
    adapter.tokenizer = Mock()
    adapter.tokenizer.encode.return_value = list(range(10))

    with caplog.at_level("INFO"):
        adapter.generate(
            SectionPrompt(SectionType.EXECUTIVE_SUMMARY, "system"),
            user_prompt="user",
        )

    assert any("Prompt tokens" in record.message and record.levelname == "INFO" for record in caplog.records)
    # Verify tokenizer was called (logging was enabled)
    assert adapter.tokenizer.encode.call_count == 2


def test_warns_on_high_token_usage(caplog: pytest.LogCaptureFixture) -> None:
    client = Mock()
    client.create_chat_completion.return_value = _make_response("ok")
    adapter = _make_adapter(client)
    adapter.tokenizer = Mock()
    adapter.tokenizer.encode.return_value = list(range(9000))

    # Need INFO level to enable token encoding, but we're checking for WARNING
    with caplog.at_level("INFO"):
        adapter.generate(
            SectionPrompt(SectionType.EXECUTIVE_SUMMARY, "system"),
            user_prompt="user",
        )

    assert any("High token usage" in record.message and record.levelname == "WARNING" for record in caplog.records)


def test_skips_token_logging_when_disabled(caplog: pytest.LogCaptureFixture) -> None:
    """Verify token encoding is skipped when log level is above INFO."""
    client = Mock()
    client.create_chat_completion.return_value = _make_response("ok")
    adapter = _make_adapter(client)
    adapter.tokenizer = Mock()
    adapter.tokenizer.encode.return_value = list(range(10))

    # Set log level to ERROR (higher than INFO) - token logging should be skipped
    with caplog.at_level("ERROR"):
        adapter.generate(
            SectionPrompt(SectionType.EXECUTIVE_SUMMARY, "system"),
            user_prompt="user",
        )

    # Verify tokenizer was NOT called (logging was disabled)
    assert adapter.tokenizer.encode.call_count == 0
    # Verify no token logging messages
    assert not any("Prompt tokens" in record.message for record in caplog.records)


def test_generate_empty_system_prompt() -> None:
    adapter = _make_adapter(Mock())

    result = adapter.generate(
        SectionPrompt(SectionType.KEY_OBSERVATIONS, " "),
        user_prompt="user",
    )

    assert result is None


def test_generate_empty_user_prompt() -> None:
    adapter = _make_adapter(Mock())

    result = adapter.generate(
        SectionPrompt(SectionType.KEY_OBSERVATIONS, "system"),
        user_prompt="",
    )

    assert result is None


def test_generate_invalid_response_shape_returns_none() -> None:
    client = Mock()
    client.create_chat_completion.return_value = Mock(spec=[])
    adapter = _make_adapter(client)

    result = adapter.generate(
        SectionPrompt(SectionType.RISK_ASSESSMENT, "system"),
        user_prompt="user",
    )

    assert result is None


@pytest.mark.parametrize(
    "error_cls",
    [
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        RateLimitError,
        APIError,
    ],
)
def test_generate_openai_errors_return_none(error_cls: type[Exception]) -> None:
    client = Mock()
    client.create_chat_completion.side_effect = _make_openai_error(error_cls, "boom")
    adapter = _make_adapter(client)

    result = adapter.generate(
        SectionPrompt(SectionType.RISK_ASSESSMENT, "system"),
        user_prompt="user",
    )

    assert result is None
