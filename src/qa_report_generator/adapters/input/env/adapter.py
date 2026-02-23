"""Environment configuration adapter."""

import logging

from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.config import EnvSettings

from .settings import load_settings_from_env

LOGGER = logging.getLogger(__name__)


def _to_app_settings(settings: EnvSettings) -> AppSettings:
    """Map validated env-settings model to the application settings DTO."""
    profile = settings.preprocessing_profile.value if settings.preprocessing_profile else None
    return AppSettings(
        log_level=settings.log_level,
        log_format=settings.log_format,
        prompt_template_path=settings.prompt_template_path,
        llm_model=settings.llm_model,
        llm_base_url=settings.llm_base_url,
        llm_api_key=settings.llm_api_key,
        llm_temperature=settings.llm_temperature,
        llm_reasoning_effort=settings.llm_reasoning_effort,
        llm_timeout=settings.llm_timeout,
        llm_max_retries=settings.llm_max_retries,
        llm_retry_backoff_factor=settings.llm_retry_backoff_factor,
        max_parallel_llm_sections=settings.max_parallel_llm_sections,
        max_output_lines_per_failure=settings.max_output_lines_per_failure,
        enable_failure_grouping=settings.enable_failure_grouping,
        failure_clustering_threshold=settings.failure_clustering_threshold,
        max_failures_for_detailed_prompt=settings.max_failures_for_detailed_prompt,
        preprocessing_profile=profile,
        plugin_modules=tuple(settings.plugin_modules),
    )


class EnvSettingsAdapter:
    """Load application settings from environment variables."""

    def load(self) -> AppSettings:
        """Load, validate, and map environment settings to the application DTO."""
        settings = load_settings_from_env()
        app_settings = _to_app_settings(settings)
        LOGGER.debug("Environment settings loaded (log_level=%s)", app_settings.log_level)
        return app_settings
