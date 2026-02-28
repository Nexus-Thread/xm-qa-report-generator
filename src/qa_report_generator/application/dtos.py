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
    prompt_template_path: str | None
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    llm_temperature: float | None
    llm_reasoning_effort: str | None
    llm_timeout: float
    llm_max_retries: int
    llm_retry_backoff_factor: float
    max_parallel_llm_sections: int
    max_output_lines_per_failure: int
    enable_failure_grouping: bool
    failure_clustering_threshold: float
    max_failures_for_detailed_prompt: int
    preprocessing_profile: str | None
    plugin_modules: tuple[str, ...]


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
    """Result metadata for a generated k6 summary table."""

    output_path: Path
    rows_count: int


@dataclass(frozen=True)
class K6ServiceExtractionResult:
    """Result metadata for a generated service extraction JSON artifact."""

    output_path: Path
    service: str
    extracted: dict[str, Any]


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
