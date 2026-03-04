"""Output port protocols for adapters used by use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.dtos import K6SummaryRow
    from qa_report_generator.domain.analytics import K6ParsedReport


class K6SummaryTableParserPort(Protocol):
    """Port for parsing raw k6 reports into summary rows."""

    def parse(self, *, report_files: list[Path]) -> list[K6SummaryRow]:
        """Parse report files into table rows."""


class K6ParsedReportParserPort(Protocol):
    """Port for parsing raw k6 reports into scenario-centric report models."""

    def parse(
        self,
        *,
        service: str,
        report_files: list[Path],
        remove_keys: frozenset[str] | None = None,
    ) -> K6ParsedReport:
        """Parse report files into parsed report domain model."""


class StructuredLlmPort(Protocol):
    """Port for deterministic JSON generation with an LLM backend."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a JSON object parsed from an LLM response."""


class DebugJsonWriterPort(Protocol):
    """Port for writing debug JSON payloads to files."""

    def write_json(self, *, label: str, payload: Any) -> Path:
        """Persist one labeled JSON payload and return file path."""
