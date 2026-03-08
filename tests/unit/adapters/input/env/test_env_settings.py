"""Unit tests for environment settings adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_report_generator.adapters.input.env import EnvSettingsAdapter
from qa_report_generator.domain.exceptions import ConfigurationError


def test_env_settings_adapter_loads_defaults_when_environment_is_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Adapter uses default values when environment overrides are absent."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_TIMEOUT", raising=False)
    monkeypatch.delenv("LLM_MAX_RETRIES", raising=False)
    monkeypatch.delenv("LLM_RETRY_BACKOFF_FACTOR", raising=False)
    monkeypatch.delenv("LLM_DEBUG_JSON_ENABLED", raising=False)
    monkeypatch.delenv("LLM_DEBUG_JSON_DIR", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("LOG_FORMAT", raising=False)

    settings = EnvSettingsAdapter().load()

    assert settings.log_level == "INFO"
    assert settings.log_format == "simple"
    assert settings.llm_model == "gpt-5.2"
    assert settings.llm_base_url == "https://api.openai.com/v1"
    assert settings.llm_api_key == "not-needed"
    assert settings.llm_timeout == 100.0
    assert settings.llm_max_retries == 3
    assert settings.llm_retry_backoff_factor == 2.0
    assert settings.llm_debug_json_enabled is False
    assert settings.llm_debug_json_dir == Path("out/debug/llm")


def test_env_settings_adapter_loads_minimal_required_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter loads minimal required settings into AppSettings."""
    monkeypatch.setenv("LLM_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_TIMEOUT", "30")
    monkeypatch.setenv("LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("LLM_RETRY_BACKOFF_FACTOR", "1.5")
    monkeypatch.setenv("LLM_DEBUG_JSON_ENABLED", "true")
    monkeypatch.setenv("LLM_DEBUG_JSON_DIR", "out/debug/custom")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LOG_FORMAT", "JSON")

    settings = EnvSettingsAdapter().load()

    assert settings.log_level == "DEBUG"
    assert settings.log_format == "json"
    assert settings.llm_model == "gpt-test"
    assert settings.llm_base_url == "https://example.test/v1"
    assert settings.llm_api_key == "secret"
    assert settings.llm_timeout == 30.0
    assert settings.llm_max_retries == 2
    assert settings.llm_retry_backoff_factor == 1.5
    assert settings.llm_debug_json_enabled is True
    assert settings.llm_debug_json_dir == Path("out/debug/custom")


def test_env_settings_adapter_raises_configuration_error_for_invalid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid LOG_LEVEL raises ConfigurationError."""
    monkeypatch.setenv("LOG_LEVEL", "invalid")

    with pytest.raises(ConfigurationError):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_raises_configuration_error_for_invalid_log_format(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid LOG_FORMAT raises ConfigurationError."""
    monkeypatch.setenv("LOG_FORMAT", "yaml")

    with pytest.raises(ConfigurationError):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_raises_configuration_error_for_non_positive_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-positive LLM_TIMEOUT raises ConfigurationError."""
    monkeypatch.setenv("LLM_TIMEOUT", "0")

    with pytest.raises(ConfigurationError):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_raises_configuration_error_for_retry_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Out-of-range LLM_MAX_RETRIES raises ConfigurationError."""
    monkeypatch.setenv("LLM_MAX_RETRIES", "11")

    with pytest.raises(ConfigurationError):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_raises_configuration_error_for_backoff_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Out-of-range LLM_RETRY_BACKOFF_FACTOR raises ConfigurationError."""
    monkeypatch.setenv("LLM_RETRY_BACKOFF_FACTOR", "0.9")

    with pytest.raises(ConfigurationError):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_trims_string_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter trims text and path values from environment variables."""
    monkeypatch.setenv("LLM_MODEL", "  gpt-trimmed  ")
    monkeypatch.setenv("LLM_BASE_URL", "  https://example.test/v1  ")
    monkeypatch.setenv("LLM_API_KEY", "  token  ")
    monkeypatch.setenv("LLM_DEBUG_JSON_DIR", "  out/debug/trimmed  ")
    monkeypatch.setenv("LOG_LEVEL", "  info  ")
    monkeypatch.setenv("LOG_FORMAT", "  JSON  ")

    settings = EnvSettingsAdapter().load()

    assert settings.llm_model == "gpt-trimmed"
    assert settings.llm_base_url == "https://example.test/v1"
    assert settings.llm_api_key == "token"
    assert settings.llm_debug_json_dir == Path("out/debug/trimmed")
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"


def test_env_settings_adapter_raises_configuration_error_for_blank_debug_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Blank LLM_DEBUG_JSON_DIR raises ConfigurationError."""
    monkeypatch.setenv("LLM_DEBUG_JSON_DIR", "   ")

    with pytest.raises(ConfigurationError):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_raises_configuration_error_for_blank_llm_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blank LLM_MODEL raises ConfigurationError with field detail."""
    monkeypatch.setenv("LLM_MODEL", "   ")

    with pytest.raises(ConfigurationError, match=r"LLM_MODEL: Value error, Value must not be blank"):
        EnvSettingsAdapter().load()
