"""K6 extraction DTOs and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeAlias

if TYPE_CHECKING:
    from collections.abc import Sequence

    from qa_report_generator.domain.analytics import (
        K6OverallExecutiveSummary,
        K6ScenarioExecutiveSummary,
        K6ThresholdSummary,
    )

JsonScalar: TypeAlias = str | int | float | bool | None
K6ExtractedPayload: TypeAlias = dict[str, Any]


@dataclass(frozen=True, slots=True)
class K6ServiceExtractionRun:
    """Final extraction payload for one output run."""

    source_report_files: tuple[str, ...]
    extracted: K6ExtractedPayload

    def __post_init__(self) -> None:
        """Normalize provenance and detach the extracted payload copy."""
        object.__setattr__(self, "source_report_files", tuple(self.source_report_files))
        object.__setattr__(self, "extracted", dict(self.extracted))


@dataclass(frozen=True, slots=True)
class K6ServiceExtractionResult:
    """Validated extraction payloads returned for one service."""

    service: str
    runs: list[K6ServiceExtractionRun]
    overall_summary: K6OverallExecutiveSummary
    scenario_summaries: list[K6ScenarioExecutiveSummary]

    def to_summary_payload(self) -> dict[str, object]:
        """Return the summary-stage payload used by adapters and debug snapshots."""
        return {
            "service": self.service,
            "overall_summary": {
                "status": self.overall_summary.status,
                "total_scenarios": self.overall_summary.total_scenarios,
                "passed_scenarios": self.overall_summary.passed_scenarios,
                "failed_scenarios": self.overall_summary.failed_scenarios,
                "unknown_scenarios": self.overall_summary.unknown_scenarios,
                "scenarios_requiring_attention": self.overall_summary.scenarios_requiring_attention,
                "executive_summary": self.overall_summary.executive_summary,
            },
            "scenario_summaries": [_serialize_scenario_summary(summary) for summary in self.scenario_summaries],
        }


@dataclass(frozen=True, slots=True)
class VerificationMismatch:
    """Mismatch discovered by verification between source and extraction."""

    field: str
    expected: JsonScalar
    actual: JsonScalar
    source_jsonpath: str
    extracted_jsonpath: str
    reason: str


def _serialize_scenario_summary(summary: K6ScenarioExecutiveSummary) -> dict[str, object]:
    """Convert one domain scenario summary into a JSON-serializable payload."""
    return {
        "scenario_name": summary.scenario_name,
        "env_name": summary.env_name,
        "source_report_files": summary.source_report_files,
        "status": summary.status,
        "executor": summary.executor,
        "rate": summary.rate,
        "duration": summary.duration,
        "pre_allocated_vus": summary.pre_allocated_vus,
        "max_vus": summary.max_vus,
        "threshold_results": _serialize_threshold_results(summary.threshold_results),
        "executive_note": summary.executive_note,
    }


def _serialize_threshold_results(
    threshold_results: Sequence[K6ThresholdSummary],
) -> list[dict[str, str]]:
    """Convert threshold summary records into stable JSON payload rows."""
    return [
        {
            "metric_key": threshold.metric_key,
            "expression": threshold.expression,
            "status": threshold.status,
        }
        for threshold in threshold_results
    ]
