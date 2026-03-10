"""Analytics models for comparing report runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

K6Status: TypeAlias = Literal["pass", "fail", "unknown"]


@dataclass(frozen=True)
class K6Scenario:
    """Parsed k6 scenario with normalized fields and raw payload."""

    source_report_file: str
    name: str
    env_name: str | None
    executor: str
    rate: float
    duration: str
    pre_allocated_vus: int
    max_vus: int
    test_run_duration_ms: float
    thresholds: dict[str, list[str]]
    metrics: dict[str, dict[str, Any]]
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class K6ParsedReport:
    """Parsed k6 report grouped as scenario records for one service."""

    service: str
    scenarios: list[K6Scenario]


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
    source_report_files: list[str]
    status: K6Status
    executor: str | None
    rate: float | None
    duration: str | None
    pre_allocated_vus: int | None
    max_vus: int | None
    threshold_results: list[K6ThresholdSummary]
    executive_note: str


@dataclass(frozen=True)
class K6OverallExecutiveSummary:
    """Executive rollup for all final scenario runs."""

    status: K6Status
    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    unknown_scenarios: int
    scenarios_requiring_attention: list[str]
    executive_summary: str
