"""Unit tests for environment configuration adapter."""

from __future__ import annotations

import pytest

from qa_report_generator.adapters.input.env import EnvSettingsAdapter, load_config_from_env
from qa_report_generator.adapters.input.env import adapter as env_adapter_module
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.config import Config, PreprocessingProfile
from qa_report_generator.domain.exceptions import ConfigurationError


def test_load_config_from_env_applies_profile_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env loader should apply preprocessing profile defaults."""
    monkeypatch.setenv("PREPROCESSING_PROFILE", PreprocessingProfile.MINIMAL.value)

    config = load_config_from_env()

    assert config.preprocessing_profile == PreprocessingProfile.MINIMAL
    assert config.max_output_lines_per_failure == 10
    assert config.enable_failure_grouping is False


def test_load_config_from_env_raises_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env loader should translate validation errors to configuration errors."""
    monkeypatch.setenv("LOG_LEVEL", "not-a-level")

    with pytest.raises(ConfigurationError):
        load_config_from_env()


def test_env_settings_adapter_delegates_to_env_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter should return mapped DTO values from the settings loader."""
    expected = Config(log_level="DEBUG")
    monkeypatch.setattr(env_adapter_module, "load_config_from_env", lambda: expected)

    settings = EnvSettingsAdapter().load()

    assert isinstance(settings, AppSettings)
    assert settings.log_level == "DEBUG"
    assert settings.llm_model == expected.llm_model
