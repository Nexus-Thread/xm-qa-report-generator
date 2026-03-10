"""Map environment settings to the AppSettings DTO."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.application.dtos import AppSettings

from .settings import load_settings_from_env

__all__ = ["EnvSettingsAdapter"]


class EnvSettingsAdapter:
    """Load AppSettings from environment-backed settings."""

    def load(self) -> AppSettings:
        """Load environment settings and map them to AppSettings DTO."""
        return load_settings_from_env().to_app_settings()
