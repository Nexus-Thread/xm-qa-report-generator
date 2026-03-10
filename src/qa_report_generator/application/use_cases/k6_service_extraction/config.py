"""Configuration types for the k6 service extraction use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.application.ports.output import DebugJsonWriterPort


@dataclass(frozen=True)
class K6ServiceExtractionDebugConfig:
    """Debug snapshot configuration for k6 service extraction."""

    model_debug_json_writer: DebugJsonWriterPort | None = None
    model_debug_json_enabled: bool = False
