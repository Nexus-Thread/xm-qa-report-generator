"""Analytics models for comparing report runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReportIdentifier:
    """Suite and test name pair used in diff outputs."""

    suite: str
    name: str


@dataclass(frozen=True)
class ReportDiff:
    """Collection of differences between two report runs."""

    new_failures: list[ReportIdentifier]
    fixed_tests: list[ReportIdentifier]
    regressions: list[ReportIdentifier]


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
