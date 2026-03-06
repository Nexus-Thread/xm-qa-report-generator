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


class InvalidK6MetricPayloadError(ReportingError):
    """Raised when a k6 metric payload has an invalid shape."""


class MissingK6MetricError(ReportingError):
    """Raised when a required k6 metric is missing from a payload."""


class MissingK6ScenarioError(ReportingError):
    """Raised when a required k6 scenario definition is missing."""
