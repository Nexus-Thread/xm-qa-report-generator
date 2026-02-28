"""Analytics models for comparing report runs."""

from __future__ import annotations

from dataclasses import dataclass


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
