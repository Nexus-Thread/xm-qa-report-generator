"""Reporting DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ReportValidationMetrics:
    """Summary metrics produced by report validation."""

    total: int
    passed: int
    failed: int
    skipped: int


@dataclass(frozen=True)
class GeneratedReportsResult:
    """Generated output paths for non-k6 report workflows."""

    summary_path: Path
    signoff_path: Path
