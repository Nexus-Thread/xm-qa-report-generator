"""Domain-level exception hierarchy."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReportingError(Exception):
    """Base error for report processing failures."""

    message: str
    suggestion: str | None = None

    def __str__(self) -> str:
        """Return the user-facing error message."""
        return self.message


class ConfigurationError(ReportingError):
    """Raised when application configuration is invalid."""


class ExtractionVerificationError(ReportingError):
    """Raised when LLM verification detects numeric mismatches."""
