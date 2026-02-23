"""Utility functions for CLI command handling."""

import dataclasses

import typer

from qa_report_generator.adapters.input.cli_adapter.formatters import ConsoleFormatter
from qa_report_generator.adapters.input.cli_adapter.types import OutputVerbosity
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.config import PROFILE_DEFAULTS, PreprocessingProfile


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


def apply_profile(profile: str | None, config: AppSettings, formatter: ConsoleFormatter) -> AppSettings:
    """Apply preprocessing profile to configuration.

    Args:
        profile: Profile name to apply
        config: Settings to derive new values from
        formatter: Console formatter for error messages

    Returns:
        New AppSettings with profile defaults applied.

    Raises:
        typer.Exit: If profile is invalid

    """
    if not profile:
        return config

    try:
        p = PreprocessingProfile(profile)
    except ValueError as exc:
        formatter.print_error(f"❌ Invalid preprocessing profile: {profile}")
        raise typer.Exit(code=1) from exc

    d = PROFILE_DEFAULTS[p]
    return dataclasses.replace(
        config,
        preprocessing_profile=p.value,
        max_output_lines_per_failure=d["max_output_lines_per_failure"],
        enable_failure_grouping=d["enable_failure_grouping"],
        failure_clustering_threshold=d["failure_clustering_threshold"],
        max_failures_for_detailed_prompt=d["max_failures_for_detailed_prompt"],
    )
