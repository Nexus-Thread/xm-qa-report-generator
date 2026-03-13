"""Output port protocols for adapters used by use cases."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from qa_report_generator_performance.application.dtos import LlmUsageSummary
    from qa_report_generator_performance.domain.analytics import K6ParsedReport


class StructuredLlmPort(Protocol):
    """Port for deterministic JSON generation with an LLM backend."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Return a JSON object parsed from an LLM response."""


class LlmUsageSummaryProviderPort(Protocol):
    """Port for resetting and reading aggregated LLM usage for one run."""

    def reset(self) -> None:
        """Clear any previously aggregated LLM usage state."""

    def build_summary(self) -> LlmUsageSummary | None:
        """Return aggregated LLM usage for the current run, if any."""


class JsonWriterPort(Protocol):
    """Port for writing labeled JSON payloads to files."""

    def write_json(self, *, label: str, payload: Any) -> Path:
        """Persist one labeled JSON payload and return file path."""


class K6ParsedReportParserPort(Protocol):
    """Port for parsing raw k6 report files into scenario-centric models."""

    def parse(
        self,
        *,
        service: str,
        report_files: Sequence[Path],
        remove_keys: frozenset[str] = frozenset(),
    ) -> K6ParsedReport:
        """Parse report files into a normalized parsed report."""
