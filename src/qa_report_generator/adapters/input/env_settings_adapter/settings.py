"""Environment-backed settings loader."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import Field, ValidationError, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.domain.exceptions import ConfigurationError

LOGGER = logging.getLogger(__name__)
ALLOWED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
ALLOWED_LOG_FORMATS = frozenset({"simple", "json"})


def _normalize_non_empty_text(value: object, *, message: str) -> object:
    """Return stripped text values and reject blanks."""
    if not isinstance(value, str):
        return value

    normalized = value.strip()
    if not normalized:
        raise ValueError(message)
    return normalized


def _normalize_path(value: object, *, field_name: str) -> object:
    """Return normalized path values and reject blank strings."""
    if isinstance(value, Path):
        return value

    normalized = _normalize_non_empty_text(value, message=f"{field_name} must not be blank")
    if not isinstance(normalized, str):
        return normalized
    return Path(normalized)


class EnvSettings(BaseSettings):
    """Application configuration loaded from environment variables or a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    log_level: str | None = Field(default=None, description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    log_format: str | None = Field(default=None, description="Logging format: 'simple' for human-readable, 'json' for structured logging")
    llm_model: str | None = Field(default=None, alias="LLM_MODEL", description="LLM model name for OpenAI-compatible endpoint")
    llm_base_url: str | None = Field(default=None, alias="LLM_BASE_URL", description="Base URL for OpenAI-compatible endpoint")
    llm_api_key: str = Field(alias="LLM_API_KEY", description="API key for OpenAI-compatible endpoint")
    llm_timeout: float | None = Field(default=None, alias="LLM_TIMEOUT", gt=0.0, description="Timeout in seconds for LLM API requests")
    llm_max_retries: int | None = Field(
        default=None,
        alias="LLM_MAX_RETRIES",
        ge=0,
        le=10,
        description="Maximum number of retry attempts for transient LLM failures",
    )
    llm_retry_backoff_factor: float | None = Field(
        default=None,
        alias="LLM_RETRY_BACKOFF_FACTOR",
        ge=1.0,
        le=10.0,
        description="Exponential backoff multiplier for retries (wait time = factor^attempt)",
    )
    llm_debug_json_enabled: bool | None = Field(
        default=None, alias="LLM_DEBUG_JSON_ENABLED", description="Enable writing structured LLM request/response/parsed payloads to JSON files"
    )
    llm_debug_json_dir: Path | None = Field(
        default=None,
        alias="LLM_DEBUG_JSON_DIR",
        description="Directory where structured LLM debug JSON payload files are written",
    )
    model_debug_json_enabled: bool | None = Field(
        default=None,
        alias="MODEL_DEBUG_JSON_ENABLED",
        description="Enable writing generated model payloads such as summary/full output JSON files",
    )
    model_debug_json_dir: Path | None = Field(
        default=None,
        alias="MODEL_DEBUG_JSON_DIR",
        description="Directory where generated model JSON payload files are written",
    )

    @field_validator("llm_model", "llm_base_url", "llm_api_key", mode="before")
    @classmethod
    def validate_non_empty_text(cls, value: object) -> object:
        """Normalize text settings and reject blank values."""
        if value is None:
            return value
        return _normalize_non_empty_text(value, message="Value must not be blank")

    @field_validator("llm_debug_json_dir", "model_debug_json_dir", mode="before")
    @classmethod
    def validate_debug_json_dir(cls, value: object, info: ValidationInfo) -> object:
        """Normalize debug output directory and reject blank values."""
        if value is None:
            return value
        field_name = info.field_name.upper() if info.field_name is not None else "PATH"
        return _normalize_path(value, field_name=field_name)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str | None) -> str | None:
        """Normalize and validate log level."""
        if value is None:
            return value
        normalized = value.strip().upper()
        if normalized not in ALLOWED_LOG_LEVELS:
            msg = f"Invalid log level: {normalized}. Must be one of: {', '.join(sorted(ALLOWED_LOG_LEVELS))}"
            raise ValueError(msg)
        return normalized

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, value: str | None) -> str | None:
        """Normalize and validate log format."""
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in ALLOWED_LOG_FORMATS:
            msg = f"Invalid log format: {normalized}. Must be one of: {', '.join(sorted(ALLOWED_LOG_FORMATS))}"
            raise ValueError(msg)
        return normalized

    def to_app_settings(self) -> AppSettings:
        """Convert validated adapter settings to the application DTO."""
        return AppSettings(**self.model_dump(exclude_none=True))


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
