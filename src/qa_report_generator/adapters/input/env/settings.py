"""Environment-backed settings loader."""

import logging

from pydantic import ValidationError

from qa_report_generator.config import EnvSettings
from qa_report_generator.domain.exceptions import ConfigurationError

LOGGER = logging.getLogger(__name__)


def load_settings_from_env() -> EnvSettings:
    """Load and validate application configuration from environment variables.

    Returns:
        Validated and profile-defaulted EnvSettings instance.

    Raises:
        ConfigurationError: If environment variables fail validation.

    """
    try:
        settings = EnvSettings()
    except ValidationError as exc:
        message = f"Invalid configuration: {exc}"
        raise ConfigurationError(message) from exc

    settings.apply_profile_defaults()
    LOGGER.debug("Configuration loaded from environment (profile=%s)", settings.preprocessing_profile)
    return settings


def load_config_from_env() -> EnvSettings:
    """Backward-compatible alias for load_settings_from_env."""
    return load_settings_from_env()
