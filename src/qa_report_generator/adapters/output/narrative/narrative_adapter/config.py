"""Technical configuration for the narrative adapter."""

import warnings

from pydantic import BaseModel, ConfigDict, Field, field_validator

LOW_TIMEOUT_WARNING_THRESHOLD = 30.0


class LLMAdapterConfig(BaseModel):
    """Technical configuration for the narrative adapter."""

    model_config = ConfigDict(extra="ignore")

    # OpenAI-compatible endpoint settings
    llm_model: str = Field(
        description="LLM model name for OpenAI-compatible endpoint",
    )
    llm_base_url: str = Field(
        description="Base URL for OpenAI-compatible endpoint",
    )
    llm_api_key: str = Field(
        description="API key for OpenAI-compatible endpoint",
    )
    llm_temperature: float | None = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 = deterministic, 1.0 = creative). Set to None to use provider default.",
    )
    llm_reasoning_effort: str | None = Field(
        default=None,
        description="Optional reasoning effort (model-specific)",
    )

    # Network and retry settings
    llm_timeout: float = Field(
        gt=0.0,
        description="Timeout in seconds for LLM API requests",
    )
    llm_max_retries: int = Field(
        ge=0,
        le=10,
        description="Maximum number of retry attempts for transient LLM failures",
    )
    llm_retry_backoff_factor: float = Field(
        ge=1.0,
        le=10.0,
        description="Exponential backoff multiplier for retries (wait time = factor^attempt)",
    )

    @property
    def base_url(self) -> str:
        """Return OpenAI-compatible base URL."""
        return self.llm_base_url

    @property
    def api_key(self) -> str:
        """Return API key for OpenAI-compatible endpoint."""
        return self.llm_api_key

    @property
    def max_retries(self) -> int:
        """Return maximum retry attempts."""
        return self.llm_max_retries

    @property
    def backoff_seconds(self) -> float:
        """Return retry backoff base duration in seconds."""
        return self.llm_retry_backoff_factor

    @property
    def verify_ssl(self) -> bool:
        """Return SSL verification flag."""
        return True

    @property
    def timeout_seconds(self) -> float:
        """Return HTTP timeout in seconds."""
        return self.llm_timeout

    @field_validator("llm_model", "llm_base_url", "llm_api_key")
    @classmethod
    def validate_required_strings(cls, v: str) -> str:
        """Ensure required string settings are not empty."""
        v = v.strip()
        if not v:
            msg = "LLM configuration values cannot be empty. Check .env file."
            raise ValueError(msg)
        return v

    @field_validator("llm_timeout")
    @classmethod
    def warn_low_timeout(cls, v: float) -> float:
        """Warn if timeout is very low.

        Args:
            v: Timeout value to check

        Returns:
            Timeout value unchanged

        """
        if v < LOW_TIMEOUT_WARNING_THRESHOLD:
            warnings.warn(
                f"⚠️  Low timeout ({v}s) detected. LLM requests may fail with timeouts "
                f"below {LOW_TIMEOUT_WARNING_THRESHOLD:.0f} seconds, especially for larger models or slower hardware. "
                f"Consider increasing to 60s or higher.",
                UserWarning,
                stacklevel=2,
            )
        return v
