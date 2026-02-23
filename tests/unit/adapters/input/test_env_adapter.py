"""Unit tests for environment configuration adapter."""

from __future__ import annotations

import pytest

from qa_report_generator.adapters.input.env import EnvSettings, EnvSettingsAdapter, load_settings_from_env
from qa_report_generator.adapters.input.env import adapter as env_adapter_module
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.config import PreprocessingProfile
from qa_report_generator.domain.exceptions import ConfigurationError

# ---------------------------------------------------------------------------
# load_settings_from_env
# ---------------------------------------------------------------------------


def test_load_settings_from_env_applies_profile_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env loader should apply preprocessing profile defaults."""
    monkeypatch.setenv("PREPROCESSING_PROFILE", PreprocessingProfile.MINIMAL.value)

    settings = load_settings_from_env()

    assert settings.preprocessing_profile == PreprocessingProfile.MINIMAL
    assert settings.max_output_lines_per_failure == 10
    assert settings.enable_failure_grouping is False


def test_load_settings_from_env_raises_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env loader should translate Pydantic validation errors to ConfigurationError."""
    monkeypatch.setenv("LOG_LEVEL", "not-a-level")

    with pytest.raises(ConfigurationError):
        load_settings_from_env()


def test_load_settings_from_env_returns_env_settings_instance() -> None:
    """load_settings_from_env should return an EnvSettings instance."""
    settings = load_settings_from_env()

    assert isinstance(settings, EnvSettings)


# ---------------------------------------------------------------------------
# EnvSettingsAdapter
# ---------------------------------------------------------------------------


def test_env_settings_adapter_returns_app_settings() -> None:
    """Adapter.load() should return an AppSettings dataclass instance."""
    settings = EnvSettingsAdapter().load()

    assert isinstance(settings, AppSettings)


def test_env_settings_adapter_maps_all_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter should return mapped DTO values from the settings loader."""
    stub = EnvSettings(log_level="DEBUG")
    monkeypatch.setattr(env_adapter_module, "load_settings_from_env", lambda: stub)

    result = EnvSettingsAdapter().load()

    assert isinstance(result, AppSettings)
    assert result.log_level == "DEBUG"
    assert result.llm_model == stub.llm_model
    assert result.llm_timeout == stub.llm_timeout
    assert result.enable_failure_grouping == stub.enable_failure_grouping


def test_env_settings_adapter_maps_preprocessing_profile_to_str(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter should demote PreprocessingProfile enum to plain str in AppSettings."""
    stub = EnvSettings(preprocessing_profile=PreprocessingProfile.DETAILED)
    monkeypatch.setattr(env_adapter_module, "load_settings_from_env", lambda: stub)

    result = EnvSettingsAdapter().load()

    assert result.preprocessing_profile == PreprocessingProfile.DETAILED.value
    assert isinstance(result.preprocessing_profile, str)


def test_env_settings_adapter_maps_none_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter should pass None through when no profile is set."""
    stub = EnvSettings(preprocessing_profile=None)
    monkeypatch.setattr(env_adapter_module, "load_settings_from_env", lambda: stub)

    result = EnvSettingsAdapter().load()

    assert result.preprocessing_profile is None


def test_env_settings_adapter_maps_plugin_modules_to_tuple(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter should convert plugin_modules list to tuple in AppSettings."""
    stub = EnvSettings(plugin_modules=["my.plugin", "other.plugin"])
    monkeypatch.setattr(env_adapter_module, "load_settings_from_env", lambda: stub)

    result = EnvSettingsAdapter().load()

    assert result.plugin_modules == ("my.plugin", "other.plugin")
    assert isinstance(result.plugin_modules, tuple)
