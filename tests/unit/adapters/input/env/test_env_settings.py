"""Unit tests for environment settings adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_report_generator.adapters.input.env_settings_adapter import EnvSettingsAdapter
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.application.exceptions import ConfigurationError

ENV_SETTING_NAMES = (
    "LLM_MODEL",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_TIMEOUT",
    "LLM_MAX_RETRIES",
    "LLM_MAX_CONCURRENCY",
    "LLM_RETRY_BACKOFF_FACTOR",
    "LLM_DEBUG_JSON_ENABLED",
    "LLM_DEBUG_JSON_DIR",
    "MODEL_DEBUG_JSON_ENABLED",
    "MODEL_DEBUG_JSON_DIR",
    "LOG_LEVEL",
    "LOG_FORMAT",
)


def _set_minimal_valid_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the minimum environment required for successful loading."""
    monkeypatch.setenv("LLM_API_KEY", "secret")


@pytest.fixture(autouse=True)
def isolate_env_settings(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Reset environment-backed settings for each test."""
    monkeypatch.chdir(tmp_path)
    for setting_name in ENV_SETTING_NAMES:
        monkeypatch.delenv(setting_name, raising=False)


def test_env_settings_adapter_requires_llm_api_key_when_environment_is_empty() -> None:
    """Empty environment raises a configuration error for the API key."""
    with pytest.raises(ConfigurationError, match=r"LLM_API_KEY: Field required"):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_loads_environment_overrides_into_app_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter loads normalized environment overrides into AppSettings."""
    monkeypatch.setenv("LLM_MODEL", "gpt-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("LLM_API_KEY", "secret")
    monkeypatch.setenv("LLM_TIMEOUT", "30")
    monkeypatch.setenv("LLM_MAX_RETRIES", "2")
    monkeypatch.setenv("LLM_MAX_CONCURRENCY", "6")
    monkeypatch.setenv("LLM_RETRY_BACKOFF_FACTOR", "1.5")
    monkeypatch.setenv("LLM_DEBUG_JSON_ENABLED", "true")
    monkeypatch.setenv("LLM_DEBUG_JSON_DIR", "out/debug/custom")
    monkeypatch.setenv("MODEL_DEBUG_JSON_ENABLED", "false")
    monkeypatch.setenv("MODEL_DEBUG_JSON_DIR", "out/debug/models-custom")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("LOG_FORMAT", "JSON")

    settings = EnvSettingsAdapter().load()

    assert settings == AppSettings(
        llm_api_key="secret",
        log_level="DEBUG",
        log_format="json",
        llm_model="gpt-test",
        llm_base_url="https://example.test/v1",
        llm_timeout=30.0,
        llm_max_retries=2,
        llm_max_concurrency=6,
        llm_retry_backoff_factor=1.5,
        llm_debug_json_enabled=True,
        llm_debug_json_dir=Path("out/debug/custom"),
        model_debug_json_enabled=False,
        model_debug_json_dir=Path("out/debug/models-custom"),
    )


def test_env_settings_adapter_preserves_dto_defaults_for_unset_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter passes only explicit env overrides to AppSettings."""
    monkeypatch.setenv("LLM_MODEL", "gpt-override")
    monkeypatch.setenv("LLM_API_KEY", "secret")

    settings = EnvSettingsAdapter().load()

    assert settings == AppSettings(llm_api_key="secret", llm_model="gpt-override")


def test_env_settings_adapter_requires_llm_api_key_when_not_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter raises ConfigurationError when LLM_API_KEY is missing."""
    monkeypatch.setenv("LLM_MODEL", "gpt-override")

    with pytest.raises(ConfigurationError, match=r"LLM_API_KEY: Field required"):
        EnvSettingsAdapter().load()


@pytest.mark.parametrize(
    ("setting_name", "value"),
    [
        ("LOG_LEVEL", "invalid"),
        ("LOG_FORMAT", "yaml"),
        ("LLM_TIMEOUT", "0"),
        ("LLM_MAX_RETRIES", "11"),
        ("LLM_MAX_CONCURRENCY", "0"),
        ("LLM_RETRY_BACKOFF_FACTOR", "0.9"),
    ],
)
def test_env_settings_adapter_raises_configuration_error_for_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
    setting_name: str,
    value: str,
) -> None:
    """Invalid environment values raise ConfigurationError."""
    _set_minimal_valid_env(monkeypatch)
    monkeypatch.setenv(setting_name, value)

    with pytest.raises(ConfigurationError, match=rf"{setting_name}:"):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_trims_string_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter trims text and path values from environment variables."""
    monkeypatch.setenv("LLM_MODEL", "  gpt-trimmed  ")
    monkeypatch.setenv("LLM_BASE_URL", "  https://example.test/v1  ")
    monkeypatch.setenv("LLM_API_KEY", "  token  ")
    monkeypatch.setenv("LLM_DEBUG_JSON_DIR", "  out/debug/trimmed  ")
    monkeypatch.setenv("MODEL_DEBUG_JSON_DIR", "  out/debug/models-trimmed  ")
    monkeypatch.setenv("LOG_LEVEL", "  info  ")
    monkeypatch.setenv("LOG_FORMAT", "  JSON  ")

    settings = EnvSettingsAdapter().load()

    assert settings.llm_model == "gpt-trimmed"
    assert settings.llm_base_url == "https://example.test/v1"
    assert settings.llm_api_key == "token"
    assert settings.llm_debug_json_dir == Path("out/debug/trimmed")
    assert settings.model_debug_json_dir == Path("out/debug/models-trimmed")
    assert settings.log_level == "INFO"
    assert settings.log_format == "json"


@pytest.mark.parametrize("setting_name", ["LLM_DEBUG_JSON_DIR", "MODEL_DEBUG_JSON_DIR"])
def test_env_settings_adapter_raises_configuration_error_for_blank_debug_dir(
    monkeypatch: pytest.MonkeyPatch,
    setting_name: str,
) -> None:
    """Blank debug output directories raise ConfigurationError."""
    _set_minimal_valid_env(monkeypatch)
    monkeypatch.setenv(setting_name, "   ")

    with pytest.raises(ConfigurationError, match=rf"{setting_name}: Value error, {setting_name} must not be blank"):
        EnvSettingsAdapter().load()


@pytest.mark.parametrize("setting_name", ["LOG_LEVEL", "LOG_FORMAT"])
def test_env_settings_adapter_raises_configuration_error_for_blank_logging_setting(
    monkeypatch: pytest.MonkeyPatch,
    setting_name: str,
) -> None:
    """Blank logging settings raise ConfigurationError with field detail."""
    _set_minimal_valid_env(monkeypatch)
    monkeypatch.setenv(setting_name, "   ")

    with pytest.raises(ConfigurationError, match=rf"{setting_name}: Value error, {setting_name} must not be blank"):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_raises_configuration_error_for_blank_llm_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blank LLM_MODEL raises ConfigurationError with field detail."""
    _set_minimal_valid_env(monkeypatch)
    monkeypatch.setenv("LLM_MODEL", "   ")

    with pytest.raises(ConfigurationError, match=r"LLM_MODEL: Value error, LLM_MODEL must not be blank"):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_raises_configuration_error_for_blank_llm_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blank LLM_API_KEY raises ConfigurationError with field detail."""
    monkeypatch.setenv("LLM_API_KEY", "   ")

    with pytest.raises(ConfigurationError, match=r"LLM_API_KEY: Value error, LLM_API_KEY must not be blank"):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_uses_default_llm_max_concurrency_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adapter preserves the DTO default concurrency when env override is absent."""
    _set_minimal_valid_env(monkeypatch)

    settings = EnvSettingsAdapter().load()

    assert settings.llm_max_concurrency == 4
