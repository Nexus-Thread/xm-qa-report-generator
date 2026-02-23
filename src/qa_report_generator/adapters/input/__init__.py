"""Driving adapters that translate external requests into application use cases."""

from qa_report_generator.adapters.input.cli_adapter import CliAdapter
from qa_report_generator.adapters.input.env import EnvSettingsAdapter

__all__ = [
    "CliAdapter",
    "EnvSettingsAdapter",
]
