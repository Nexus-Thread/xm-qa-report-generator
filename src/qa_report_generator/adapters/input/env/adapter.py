"""Environment configuration adapter."""

from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.config import Config

from .settings import load_config_from_env


def _to_app_settings(config: Config) -> AppSettings:
    """Map validated config model to application settings DTO."""
    profile = config.preprocessing_profile.value if config.preprocessing_profile else None
    return AppSettings(
        log_level=config.log_level,
        log_format=config.log_format,
        prompt_template_path=config.prompt_template_path,
        llm_model=config.llm_model,
        llm_base_url=config.llm_base_url,
        llm_api_key=config.llm_api_key,
        llm_temperature=config.llm_temperature,
        llm_reasoning_effort=config.llm_reasoning_effort,
        llm_timeout=config.llm_timeout,
        llm_max_retries=config.llm_max_retries,
        llm_retry_backoff_factor=config.llm_retry_backoff_factor,
        max_parallel_llm_sections=config.max_parallel_llm_sections,
        max_output_lines_per_failure=config.max_output_lines_per_failure,
        enable_failure_grouping=config.enable_failure_grouping,
        failure_clustering_threshold=config.failure_clustering_threshold,
        max_failures_for_detailed_prompt=config.max_failures_for_detailed_prompt,
        preprocessing_profile=profile,
        plugin_modules=tuple(config.plugin_modules),
    )


class EnvSettingsAdapter:
    """Load application settings from environment variables."""

    def load(self) -> AppSettings:
        """Load and validate environment settings."""
        return _to_app_settings(load_config_from_env())
