"""Environment-backed settings loader."""

import logging

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from qa_report_generator.domain.exceptions import ConfigurationError

LOGGER = logging.getLogger(__name__)


class EnvSettings(BaseSettings):
    """Application configuration loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="simple",
        description="Logging format: 'simple' for human-readable, 'json' for structured logging",
    )
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

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate the log level against allowed values.

        Args:
            v: Log level to validate

        Returns:
            Validated log level in uppercase

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
            Validated log format in lowercase

        """
        v = v.lower()
        allowed_formats = {"simple", "json"}
        if v not in allowed_formats:
            msg = f"Invalid log format: {v}. Must be one of: {', '.join(sorted(allowed_formats))}"
            raise ValueError(msg)
        return v


def load_settings_from_env() -> EnvSettings:
    """Load and validate application configuration from environment variables.

    Returns:
        Validated EnvSettings instance.

    Raises:
        ConfigurationError: If environment variables fail validation.

    """
    try:
        settings = EnvSettings()
    except ValidationError as exc:
        message = f"Invalid configuration: {exc}"
        raise ConfigurationError(message) from exc

    LOGGER.debug("Configuration loaded from environment")
    return settings
