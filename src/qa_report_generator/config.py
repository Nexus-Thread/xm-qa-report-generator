"""Business-level configuration for the reporting PoC.

This module contains application settings such as logging, prompt templates,
and LLM defaults used to instantiate adapter configuration in the composition
root. Adapter-level configs should be constructed from this model.
"""

import logging
from enum import StrEnum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class PreprocessingProfile(StrEnum):
    """Predefined preprocessing profiles for report generation."""

    MINIMAL = "minimal"
    BALANCED = "balanced"
    DETAILED = "detailed"


class Config(BaseSettings):
    """Business-level application configuration.

    Contains application settings like logging, prompt templates, and LLM defaults
    used to instantiate adapter configuration in the composition root.

    Loads configuration from environment variables or a .env file.

    Example:
        >>> config = Config()
        >>> config.log_level
        'INFO'
        >>> import os
        >>> os.environ["LOG_LEVEL"] = "DEBUG"
        >>> Config().log_level
        'DEBUG'

    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    # Application settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="simple",
        description="Logging format: 'simple' for human-readable, 'json' for structured logging",
    )

    # Business logic settings
    prompt_template_path: str | None = Field(
        default=None,
        description="Path to custom prompt template YAML file (uses built-in templates if not specified)",
    )

    # LLM adapter settings (loaded here to wire adapter config in the composition root)
    llm_model: str = Field(
        default="gpt-5.2",
        alias="LLM_MODEL",
        description="LLM model name for OpenAI-compatible endpoint",
    )
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="LLM_BASE_URL",
        description="Base URL for OpenAI-compatible endpoint",
    )
    llm_api_key: str = Field(
        default="not-needed",
        alias="LLM_API_KEY",
        description="API key for OpenAI-compatible endpoint",
    )
    llm_temperature: float | None = Field(
        default=None,
        alias="LLM_TEMPERATURE",
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 = deterministic, 1.0 = creative). Set to None for provider default.",
    )
    llm_reasoning_effort: str | None = Field(
        default=None,
        alias="LLM_REASONING_EFFORT",
        description="Optional reasoning effort (model-specific)",
    )
    llm_timeout: float = Field(
        default=100.0,
        alias="LLM_TIMEOUT",
        gt=0.0,
        description="Timeout in seconds for LLM API requests",
    )
    llm_max_retries: int = Field(
        default=3,
        alias="LLM_MAX_RETRIES",
        ge=0,
        le=10,
        description="Maximum number of retry attempts for transient LLM failures",
    )
    llm_retry_backoff_factor: float = Field(
        default=2.0,
        alias="LLM_RETRY_BACKOFF_FACTOR",
        ge=1.0,
        le=10.0,
        description="Exponential backoff multiplier for retries (wait time = factor^attempt)",
    )
    max_parallel_llm_sections: int = Field(
        default=1,
        alias="MAX_PARALLEL_LLM_SECTIONS",
        ge=1,
        le=10,
        description="Maximum number of LLM sections to generate in parallel",
    )

    max_output_lines_per_failure: int = Field(
        default=20,
        ge=1,
        le=200,
        description="Maximum output lines per failure for prompt payloads",
    )
    enable_failure_grouping: bool = Field(
        default=True,
        description="Enable grouping failures by pattern for prompt optimization",
    )
    failure_clustering_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for clustering failures",
    )
    max_failures_for_detailed_prompt: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Maximum failures to include in detailed prompt payloads",
    )

    preprocessing_profile: PreprocessingProfile | None = Field(
        default=None,
        description="Optional preprocessing profile preset (minimal, balanced, detailed)",
    )

    plugin_modules: list[str] = Field(
        default_factory=list,
        description=("Optional list of plugin module paths to import at startup. Use this to ensure decorator-based plugins are registered."),
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate the log level against allowed values.

        Args:
            v: Log level to validate

        Returns:
            Validated log level in uppercase.

        Raises:
            ValueError: If log level is not recognized.

        """
        v = v.upper()
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v not in allowed_levels:
            msg = f"Invalid log level: {v}. Must be one of: {', '.join(sorted(allowed_levels))}"
            raise ValueError(msg)

        return v

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Validate the log format against allowed values.

        Args:
            v: Log format to validate

        Returns:
            Validated log format in lowercase.

        Raises:
            ValueError: If log format is not recognized.

        """
        v = v.lower()
        allowed_formats = {"simple", "json"}
        if v not in allowed_formats:
            msg = f"Invalid log format: {v}. Must be one of: {', '.join(sorted(allowed_formats))}"
            raise ValueError(msg)

        return v

    def apply_profile_defaults(self) -> None:
        """Apply preprocessing profile defaults when configured."""
        if self.preprocessing_profile is None:
            return

        defaults = {
            PreprocessingProfile.MINIMAL: {
                "max_output_lines_per_failure": 10,
                "enable_failure_grouping": False,
                "failure_clustering_threshold": 0.85,
                "max_failures_for_detailed_prompt": 5,
            },
            PreprocessingProfile.BALANCED: {
                "max_output_lines_per_failure": 20,
                "enable_failure_grouping": True,
                "failure_clustering_threshold": 0.7,
                "max_failures_for_detailed_prompt": 10,
            },
            PreprocessingProfile.DETAILED: {
                "max_output_lines_per_failure": 30,
                "enable_failure_grouping": True,
                "failure_clustering_threshold": 0.6,
                "max_failures_for_detailed_prompt": 15,
            },
        }

        profile_defaults = defaults[self.preprocessing_profile]
        for field_name, value in profile_defaults.items():
            if field_name not in self.model_fields_set:
                setattr(self, field_name, value)
