"""Utility functions for CLI command handling."""

import typer

from qa_report_generator.adapters.input.cli_adapter.formatters import ConsoleFormatter
from qa_report_generator.adapters.input.cli_adapter.types import OutputVerbosity
from qa_report_generator.config import Config, PreprocessingProfile


def resolve_verbosity(*, verbose: bool, quiet: bool, formatter: ConsoleFormatter) -> OutputVerbosity:
    """Resolve verbosity level from CLI flags.

    Args:
        verbose: Whether verbose mode is enabled
        quiet: Whether quiet mode is enabled
        formatter: Console formatter for error messages

    Returns:
        Resolved verbosity level

    Raises:
        typer.Exit: If both flags are set

    """
    if quiet and verbose:
        formatter.print_error("❌ Cannot use both --quiet and --verbose flags")
        raise typer.Exit(code=1)
    if verbose:
        return OutputVerbosity.VERBOSE
    if quiet:
        return OutputVerbosity.QUIET
    return OutputVerbosity.NORMAL


def apply_profile(profile: str | None, config: Config, formatter: ConsoleFormatter) -> None:
    """Apply preprocessing profile to configuration.

    Args:
        profile: Profile name to apply
        config: Configuration object to modify
        formatter: Console formatter for error messages

    Raises:
        typer.Exit: If profile is invalid

    """
    if not profile:
        return

    try:
        config.preprocessing_profile = PreprocessingProfile(profile)
        config.apply_profile_defaults()
    except ValueError as exc:
        formatter.print_error(f"❌ Invalid preprocessing profile: {profile}")
        raise typer.Exit(code=1) from exc
