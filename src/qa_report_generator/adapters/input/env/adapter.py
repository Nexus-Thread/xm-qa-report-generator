"""Environment configuration adapter: maps EnvSettings to AppSettings DTO."""

from __future__ import annotations

from qa_report_generator.application.dtos import AppSettings

from .settings import load_settings_from_env

__all__ = ["EnvSettingsAdapter", "load_settings_from_env"]


class EnvSettingsAdapter:
    """Input adapter that loads AppSettings from environment variables."""

    def load(self) -> AppSettings:
        """Load and map environment settings to AppSettings DTO.

        Returns:
            Immutable AppSettings populated from the current environment.

        """
        settings = load_settings_from_env()
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
            preprocessing_profile=(settings.preprocessing_profile.value if settings.preprocessing_profile is not None else None),
            plugin_modules=tuple(settings.plugin_modules),
        )
