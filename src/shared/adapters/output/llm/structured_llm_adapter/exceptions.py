"""Exception types for shared structured LLM adapters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StructuredLlmError(Exception):
    """Base error for structured LLM adapter failures."""

    message: str
    suggestion: str | None = None

    def __str__(self) -> str:
        """Return the user-facing error message."""
        return self.message


class StructuredLlmResponseError(StructuredLlmError):
    """Raised when an LLM response is missing required content."""


class StructuredLlmInvalidJsonError(StructuredLlmError):
    """Raised when an LLM response cannot be parsed as a JSON object."""
