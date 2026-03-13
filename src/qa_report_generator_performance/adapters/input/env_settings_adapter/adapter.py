"""Map environment settings to the AppSettings DTO."""

from qa_report_generator_performance.application.dtos import AppSettings

from .settings import EnvSettings, load_settings_from_env

__all__ = ["EnvSettingsAdapter"]


def _to_app_settings(settings: EnvSettings) -> AppSettings:
    """Map validated environment settings into the application DTO."""
    return AppSettings(**settings.model_dump(exclude_none=True))


class EnvSettingsAdapter:
    """Load AppSettings from environment-backed settings."""

    def load(self) -> AppSettings:
        """Load environment settings and map them to AppSettings DTO."""
        return _to_app_settings(load_settings_from_env())
