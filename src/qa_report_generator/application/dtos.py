"""Application DTOs for settings and extraction results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    """Runtime configuration consumed by application services."""

    log_level: str
    log_format: str
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    llm_timeout: float
    llm_max_retries: int
    llm_retry_backoff_factor: float


@dataclass(frozen=True)
class K6SummaryRow:
    """Single row in the generated consolidated k6 summary table."""

    report_file: str
    scenario: str
    request_rate: float
    iterations: int
    p95_duration_ms: float
    p99_duration_ms: float
    checks_rate: float


@dataclass(frozen=True)
class K6SummaryTableResult:
    """Parsed rows returned by the k6 summary table use case."""

    rows: list[K6SummaryRow]


@dataclass(frozen=True)
class K6ServiceExtractionRun:
    """Validated extraction payload for one input report file."""

    report_file: str
    extracted: dict[str, Any]


@dataclass(frozen=True)
class K6ServiceExtractionResult:
    """Validated extraction payloads returned for one service."""

    service: str
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
