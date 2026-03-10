"""Environment-backed settings loader."""

import logging
from pathlib import Path

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from qa_report_generator.domain.exceptions import ConfigurationError

LOGGER = logging.getLogger(__name__)
ALLOWED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
ALLOWED_LOG_FORMATS = frozenset({"simple", "json"})


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
    llm_debug_json_enabled: bool = Field(
        default=False,
        alias="LLM_DEBUG_JSON_ENABLED",
        description="Enable writing structured LLM request/response/parsed payloads to JSON files",
    )
    llm_debug_json_dir: Path = Field(
        default=Path("out/debug/llm"),
        alias="LLM_DEBUG_JSON_DIR",
        description="Directory where structured LLM debug JSON payload files are written",
    )
    model_debug_json_enabled: bool = Field(
        default=True,
        alias="MODEL_DEBUG_JSON_ENABLED",
        description="Enable writing generated model payloads such as summary/full output JSON files",
    )
    model_debug_json_dir: Path = Field(
        default=Path("out/debug/models"),
        alias="MODEL_DEBUG_JSON_DIR",
        description="Directory where generated model JSON payload files are written",
    )

    @field_validator("llm_model", "llm_base_url", "llm_api_key", mode="before")
    @classmethod
    def validate_non_empty_text(cls, value: object) -> object:
        """Normalize text settings and reject blank values."""
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            msg = "Value must not be blank"
            raise ValueError(msg)
        return normalized

    @field_validator("llm_debug_json_dir", mode="before")
    @classmethod
    def validate_llm_debug_json_dir(cls, value: object) -> object:
        """Normalize debug output directory and reject blank values."""
        if isinstance(value, Path):
            return value
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            msg = "LLM_DEBUG_JSON_DIR must not be blank"
            raise ValueError(msg)
        return Path(normalized)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Normalize and validate log level."""
        v = v.strip().upper()
        if v not in ALLOWED_LOG_LEVELS:
            msg = f"Invalid log level: {v}. Must be one of: {', '.join(sorted(ALLOWED_LOG_LEVELS))}"
            raise ValueError(msg)
        return v

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        """Normalize and validate log format."""
        v = v.strip().lower()
        if v not in ALLOWED_LOG_FORMATS:
            msg = f"Invalid log format: {v}. Must be one of: {', '.join(sorted(ALLOWED_LOG_FORMATS))}"
            raise ValueError(msg)
        return v

    @field_validator("model_debug_json_dir", mode="before")
    @classmethod
    def validate_model_debug_json_dir(cls, value: object) -> object:
        """Normalize model output directory and reject blank values."""
        if isinstance(value, Path):
            return value
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        if not normalized:
            msg = "MODEL_DEBUG_JSON_DIR must not be blank"
            raise ValueError(msg)
        return Path(normalized)


def _build_validation_error_details(error: ValidationError) -> str:
    """Format pydantic validation errors for configuration failures."""
    return "; ".join(f"{'.'.join(str(part) for part in validation_error['loc'])}: {validation_error['msg']}" for validation_error in error.errors())


def load_settings_from_env() -> EnvSettings:
    """Load and validate application configuration from environment variables."""
    try:
        settings = EnvSettings()
    except ValidationError as exc:
        message = f"Invalid configuration: {_build_validation_error_details(exc)}"
        raise ConfigurationError(message) from exc

    LOGGER.debug("Configuration loaded from environment")
    return settings
