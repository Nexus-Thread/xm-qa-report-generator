"""Driving adapters that translate external requests into application use cases."""

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.adapters.input.env_settings_adapter import EnvSettingsAdapter

__all__ = [
    "EnvSettingsAdapter",
    "K6CliAdapter",
]
