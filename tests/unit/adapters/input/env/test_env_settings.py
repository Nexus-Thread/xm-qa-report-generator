"""Unit tests for environment settings adapter."""

from __future__ import annotations

import pytest

from qa_report_generator.adapters.input.env import EnvSettingsAdapter
from qa_report_generator.domain.exceptions import ConfigurationError


def test_env_settings_adapter_loads_minimal_required_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter loads minimal required settings into AppSettings."""
    monkeypatch.setenv("LLM_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_TIMEOUT", "30")
    monkeypatch.setenv("LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("LLM_RETRY_BACKOFF_FACTOR", "1.5")
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


def test_env_settings_adapter_raises_configuration_error_for_invalid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid LOG_LEVEL raises ConfigurationError."""
    monkeypatch.setenv("LOG_LEVEL", "invalid")

    with pytest.raises(ConfigurationError):
        EnvSettingsAdapter().load()
