"""K6 extraction DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

if TYPE_CHECKING:
    from qa_report_generator.domain.analytics import (
        K6OverallExecutiveSummary,
        K6ScenarioExecutiveSummary,
    )

JsonScalar: TypeAlias = str | int | float | bool | None
ExtractionMode: TypeAlias = Literal["generic", "service_specific"]


@dataclass(frozen=True)
class K6ServiceExtractionRun:
    """Final extraction payload for one output run."""

    source_report_files: list[str]
    extracted: dict[str, Any]


@dataclass(frozen=True)
class K6ServiceExtractionResult:
    """Validated extraction payloads returned for one service."""

    service: str
    mode: ExtractionMode
    runs: list[K6ServiceExtractionRun]
    overall_summary: K6OverallExecutiveSummary
    scenario_summaries: list[K6ScenarioExecutiveSummary]


@dataclass(frozen=True)
class VerificationMismatch:
    """Mismatch discovered by verification between source and extraction."""

    field: str
    expected: JsonScalar
    actual: JsonScalar
    source_jsonpath: str
    extracted_jsonpath: str
    reason: str
