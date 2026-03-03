"""Output port protocols for adapters used by use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.dtos import K6SummaryRow


class K6SummaryTableParserPort(Protocol):
    """Port for parsing raw k6 reports into summary rows."""

    def parse(self, *, report_files: list[Path]) -> list[K6SummaryRow]:
        """Parse report files into table rows."""


class StructuredLlmPort(Protocol):
    """Port for deterministic JSON generation with an LLM backend."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a JSON object parsed from an LLM response."""


class DebugJsonWriterPort(Protocol):
    """Port for writing debug JSON payloads to files."""

    def write_json(self, *, label: str, payload: Any) -> Path:
        """Persist one labeled JSON payload and return file path."""
