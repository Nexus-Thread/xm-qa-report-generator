"""Analytics models for comparing report runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

K6Status: TypeAlias = Literal["pass", "fail", "unknown"]


@dataclass(frozen=True)
class K6Scenario:
    """Parsed k6 scenario with provenance and raw source payload."""

    source_report_file: str
    name: str
    source_payload: dict[str, Any]


@dataclass(frozen=True)
class K6ParsedReport:
    """Parsed k6 report grouped as scenario records for one service."""

    service: str
    scenarios: tuple[K6Scenario, ...]

    def __post_init__(self) -> None:
        """Normalize mutable collections into immutable tuples."""
        object.__setattr__(self, "scenarios", tuple(self.scenarios))


@dataclass(frozen=True)
class K6ThresholdSummary:
    """Executive threshold view for one metric expression."""

    metric_key: str
    expression: str
    status: K6Status


@dataclass(frozen=True)
class K6ScenarioExecutiveSummary:
    """Executive summary row for one final scenario run."""

    scenario_name: str
    env_name: str | None
    source_report_files: tuple[str, ...]
    status: K6Status
    executor: str | None
    rate: float | None
    duration: str | None
    pre_allocated_vus: int | None
    max_vus: int | None
    threshold_results: tuple[K6ThresholdSummary, ...]
    executive_note: str

    def __post_init__(self) -> None:
        """Normalize mutable collections into immutable tuples."""
        object.__setattr__(self, "source_report_files", tuple(self.source_report_files))
        object.__setattr__(self, "threshold_results", tuple(self.threshold_results))


@dataclass(frozen=True)
class K6OverallExecutiveSummary:
    """Executive rollup for all final scenario runs."""

    status: K6Status
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    unknown_scenarios: int
    scenarios_requiring_attention: tuple[str, ...]
    executive_summary: str

    def __post_init__(self) -> None:
        """Normalize mutable collections into immutable tuples."""
        object.__setattr__(self, "scenarios_requiring_attention", tuple(self.scenarios_requiring_attention))
