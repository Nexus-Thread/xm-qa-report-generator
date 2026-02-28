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


class K6SummaryTableWriterPort(Protocol):
    """Port for writing consolidated summary rows."""

    def write(self, *, rows: list[K6SummaryRow], output_path: Path) -> Path:
        """Write summary rows to an output file."""


class ExtractedMetricsWriterPort(Protocol):
    """Port for persisting extracted service-specific metrics."""

    def write(self, *, data: dict[str, Any], output_path: Path) -> Path:
        """Write extracted JSON payload to an output file."""


class StructuredLlmPort(Protocol):
    """Port for deterministic JSON generation with an LLM backend."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a JSON object parsed from an LLM response."""
