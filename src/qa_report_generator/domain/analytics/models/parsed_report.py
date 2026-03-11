"""Domain records for parsed k6 reports and scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
