"""Environment-backed settings helpers."""

from pydantic import ValidationError

from qa_report_generator.config import Config
from qa_report_generator.domain.exceptions import ConfigurationError


def load_config_from_env() -> Config:
    """Load and validate application configuration from environment variables."""
    try:
        config = Config()
    except ValidationError as exc:
        message = f"Invalid configuration: {exc}"
        raise ConfigurationError(message) from exc

    config.apply_profile_defaults()
    return config
