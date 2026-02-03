"""Unit tests for the LLMAdapter narrative adapter."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError

from qa_report_generator.adapters.output.narrative import LLMAdapter, LLMAdapterConfig
from qa_report_generator.domain.exceptions import GenerationError
from qa_report_generator.domain.models import EnvironmentMeta, ReportFacts, RunMetrics
from qa_report_generator.domain.value_objects import Duration, SectionType


@pytest.fixture
def facts() -> ReportFacts:
    metrics = RunMetrics(
        total=1,
        passed=1,
        failed=0,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.2),
        failures=[],
    )
    return ReportFacts(
        metrics=metrics,
        environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
        input_files=["report.json"],
    )


def _make_adapter(client: Mock, **overrides: Any) -> LLMAdapter:
    defaults = {
        "llm_model": "test-model",
        "llm_base_url": "http://test",
        "llm_api_key": "not-needed",
        "llm_temperature": 0.2,
        "llm_reasoning_effort": None,
        "llm_timeout": 30.0,
        "llm_max_retries": 1,
        "llm_retry_backoff_factor": 2.0,
    }
    defaults.update(overrides)
    config = LLMAdapterConfig(**defaults)
    return LLMAdapter(config, client=client)


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
    client.chat.completions.create.return_value = _make_response("hello")
    adapter = _make_adapter(client)
    adapter.tokenizer = Mock()
    adapter.tokenizer.encode.return_value = list(range(12))

    # Enable INFO logging to trigger token encoding
    with caplog.at_level("INFO"):
        result = adapter.generate(
            SectionType.EXECUTIVE_SUMMARY,
            system_prompt="system",
            user_prompt="user",
        )

    assert result == "hello"
    client.chat.completions.create.assert_called_once()
    adapter.tokenizer.encode.assert_any_call("system")
    adapter.tokenizer.encode.assert_any_call("user")


def test_logs_token_usage_at_info(caplog: pytest.LogCaptureFixture) -> None:
    client = Mock()
    client.chat.completions.create.return_value = _make_response("ok")
    adapter = _make_adapter(client)
    adapter.tokenizer = Mock()
    adapter.tokenizer.encode.return_value = list(range(10))

    with caplog.at_level("INFO"):
        adapter.generate(
            SectionType.EXECUTIVE_SUMMARY,
            system_prompt="system",
            user_prompt="user",
        )

    assert any("Prompt tokens" in record.message and record.levelname == "INFO" for record in caplog.records)
    # Verify tokenizer was called (logging was enabled)
    assert adapter.tokenizer.encode.call_count == 2


def test_warns_on_high_token_usage(caplog: pytest.LogCaptureFixture) -> None:
    client = Mock()
    client.chat.completions.create.return_value = _make_response("ok")
    adapter = _make_adapter(client)
    adapter.tokenizer = Mock()
    adapter.tokenizer.encode.return_value = list(range(9000))

    # Need INFO level to enable token encoding, but we're checking for WARNING
    with caplog.at_level("INFO"):
        adapter.generate(
            SectionType.EXECUTIVE_SUMMARY,
            system_prompt="system",
            user_prompt="user",
        )

    assert any("High token usage" in record.message and record.levelname == "WARNING" for record in caplog.records)


def test_skips_token_logging_when_disabled(caplog: pytest.LogCaptureFixture) -> None:
    """Verify token encoding is skipped when log level is above INFO."""
    client = Mock()
    client.chat.completions.create.return_value = _make_response("ok")
    adapter = _make_adapter(client)
    adapter.tokenizer = Mock()
    adapter.tokenizer.encode.return_value = list(range(10))

    # Set log level to ERROR (higher than INFO) - token logging should be skipped
    with caplog.at_level("ERROR"):
        adapter.generate(
            SectionType.EXECUTIVE_SUMMARY,
            system_prompt="system",
            user_prompt="user",
        )

    # Verify tokenizer was NOT called (logging was disabled)
    assert adapter.tokenizer.encode.call_count == 0
    # Verify no token logging messages
    assert not any("Prompt tokens" in record.message for record in caplog.records)


def test_generate_empty_system_prompt() -> None:
    adapter = _make_adapter(Mock())

    result = adapter.generate(
        SectionType.KEY_OBSERVATIONS,
        system_prompt=" ",
        user_prompt="user",
    )

    assert result is None


def test_generate_empty_user_prompt() -> None:
    adapter = _make_adapter(Mock())

    result = adapter.generate(
        SectionType.KEY_OBSERVATIONS,
        system_prompt="system",
        user_prompt="",
    )

    assert result is None


def test_chat_completion_retries_and_succeeds() -> None:
    client = Mock()
    client.chat.completions.create.side_effect = [
        _make_openai_error(APIConnectionError, "boom"),
        _make_response("ok"),
    ]
    adapter = _make_adapter(client, llm_max_retries=2)

    result = adapter.generate(
        SectionType.RISK_ASSESSMENT,
        system_prompt="system",
        user_prompt="user",
    )

    assert result == "ok"
    assert client.chat.completions.create.call_count == 2


def test_chat_completion_rate_limit_exhausted() -> None:
    client = Mock()
    client.chat.completions.create.side_effect = _make_openai_error(RateLimitError, "limit")
    adapter = _make_adapter(client, llm_max_retries=1)

    with pytest.raises(GenerationError):
        adapter.retry_handler.chat_completion(
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
            temperature=0.4,
        )


def test_chat_completion_timeout_raises() -> None:
    client = Mock()
    client.chat.completions.create.side_effect = _make_openai_error(APITimeoutError, "timeout")
    adapter = _make_adapter(client, llm_max_retries=0)
    adapter.client.timeout = 15

    with pytest.raises(GenerationError):
        adapter.retry_handler.chat_completion(
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
            temperature=0.4,
        )


def test_chat_completion_invalid_messages() -> None:
    adapter = _make_adapter(Mock())

    with pytest.raises(GenerationError):
        adapter.retry_handler.chat_completion(messages=[], temperature=0.0)

    with pytest.raises(GenerationError):
        adapter.retry_handler.chat_completion(
            messages=[{"role": "user", "content": " "}],
            temperature=0.0,
        )


def test_chat_completion_auth_failure() -> None:
    client = Mock()
    client.chat.completions.create.side_effect = _make_openai_error(AuthenticationError, "bad-key")
    adapter = _make_adapter(client)

    with pytest.raises(GenerationError):
        adapter.retry_handler.chat_completion(
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
            temperature=0.4,
        )
