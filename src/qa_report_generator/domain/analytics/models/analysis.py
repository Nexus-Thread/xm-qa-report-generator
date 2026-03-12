"""Domain analysis models for k6 reporting outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .summary import K6Status, K6ThresholdSummary


@dataclass(frozen=True)
class K6ScenarioAnalysis:
    """Derived analysis facts for one final scenario run."""

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
    failing_thresholds: tuple[str, ...]

    def __post_init__(self) -> None:
        """Normalize mutable collections into immutable tuples."""
        object.__setattr__(self, "source_report_files", tuple(self.source_report_files))
        object.__setattr__(self, "threshold_results", tuple(self.threshold_results))
        object.__setattr__(self, "failing_thresholds", tuple(self.failing_thresholds))


@dataclass(frozen=True)
class K6OverallAnalysis:
    """Derived analysis facts aggregated across all final scenario runs."""

    status: K6Status
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    unknown_scenarios: int
    scenarios_requiring_attention: tuple[str, ...]

    def __post_init__(self) -> None:
        """Normalize mutable collections into immutable tuples."""
        object.__setattr__(self, "scenarios_requiring_attention", tuple(self.scenarios_requiring_attention))
