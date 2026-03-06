"""Map environment settings to the AppSettings DTO."""

from __future__ import annotations

from qa_report_generator.application.dtos import AppSettings

from .settings import load_settings_from_env

__all__ = ["EnvSettingsAdapter"]


class EnvSettingsAdapter:
    """Load AppSettings from environment-backed settings."""

    def load(self) -> AppSettings:
        """Load environment settings and map them to AppSettings DTO."""
        settings = load_settings_from_env()
        return AppSettings(
            log_level=settings.log_level,
            log_format=settings.log_format,
            llm_model=settings.llm_model,
            llm_base_url=settings.llm_base_url,
            llm_api_key=settings.llm_api_key,
            llm_timeout=settings.llm_timeout,
            llm_max_retries=settings.llm_max_retries,
            llm_retry_backoff_factor=settings.llm_retry_backoff_factor,
            llm_debug_json_enabled=settings.llm_debug_json_enabled,
            llm_debug_json_dir=settings.llm_debug_json_dir,
        )
