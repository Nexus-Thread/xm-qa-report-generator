"""K6 extraction DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class K6ServiceExtractionRun:
    """Validated extraction payload for one input report file."""

    report_file: str
    extracted: dict[str, Any]


@dataclass(frozen=True)
class K6ServiceExtractionResult:
    """Validated extraction payloads returned for one service."""

    service: str
    mode: str
    extracted_runs: list[K6ServiceExtractionRun]


@dataclass(frozen=True)
class VerificationMismatch:
    """Mismatch discovered by verification between source and extraction."""

    field: str
    expected: str
    actual: str
    source_jsonpath: str
    extracted_jsonpath: str
    reason: str
