"""Logging helpers for the structured LLM adapter."""

from __future__ import annotations

MAX_LOG_PREVIEW_CHARS = 10_000


def truncate_for_log(value: str, *, max_chars: int = MAX_LOG_PREVIEW_CHARS) -> tuple[str, bool]:
    """Return truncated log preview and truncation flag."""
    if len(value) <= max_chars:
        return value, False
    return f"{value[:max_chars]}...[truncated]", True
