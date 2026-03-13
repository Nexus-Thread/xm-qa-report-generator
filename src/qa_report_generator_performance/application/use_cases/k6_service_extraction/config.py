"""Configuration types for the k6 service extraction use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator_performance.application.ports.output import JsonWriterPort, LlmUsageSummaryProviderPort


@dataclass(frozen=True)
class K6ServiceExtractionDebugConfig:
    """Debug snapshot configuration for k6 service extraction."""

    model_debug_json_writer: JsonWriterPort | None = None
    model_debug_json_enabled: bool = False


@dataclass(frozen=True)
class K6ServiceExtractionRuntimeConfig:
    """Runtime configuration for k6 service extraction orchestration."""

    llm_usage_summary_provider: LlmUsageSummaryProviderPort | None = None
    max_parallel_scenarios: int = 1
    max_verification_attempts: int = 3
