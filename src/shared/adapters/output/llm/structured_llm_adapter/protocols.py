"""Protocols used by shared structured LLM adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class JsonDebugWriterProtocol(Protocol):
    """Protocol for optional debug JSON payload persistence."""

    def write_json(self, *, label: str, payload: Any) -> Path:
        """Persist one labeled JSON payload and return file path."""
