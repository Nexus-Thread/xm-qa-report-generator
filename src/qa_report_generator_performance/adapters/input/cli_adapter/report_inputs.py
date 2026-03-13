"""CLI input normalization helpers for report extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class CliInputError(ValueError):
    """Raised when CLI input validation fails."""


def normalize_service_input(service: str) -> str:
    """Normalize and validate the service identifier."""
    normalized_service = service.strip()
    if not normalized_service:
        msg = "--service cannot be empty"
        raise CliInputError(msg)
    return normalized_service


def expand_report_inputs(report_inputs: list[Path]) -> list[Path]:
    """Resolve report inputs into a sorted de-duplicated file list."""
    if not report_inputs:
        msg = "At least one --report input is required"
        raise CliInputError(msg)

    resolved_files: set[Path] = set()
    for report_input in report_inputs:
        resolved_files.update(_expand_report_input(report_input))
    return sorted(resolved_files)


def _expand_report_input(report_input: Path) -> list[Path]:
    """Expand one report input into concrete JSON files."""
    if report_input.is_dir():
        directory_files = sorted(path for path in report_input.glob("*.json") if path.is_file())
        if not directory_files:
            msg = f"No JSON report files found in directory: {report_input}"
            raise CliInputError(msg)
        return directory_files

    if report_input.is_file():
        if report_input.suffix.lower() != ".json":
            msg = f"Report file must be a JSON file: {report_input}"
            raise CliInputError(msg)
        return [report_input]

    msg = f"Invalid report input: {report_input}"
    raise CliInputError(msg)
