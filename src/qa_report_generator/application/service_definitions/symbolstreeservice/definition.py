"""Symbolstreeservice service extraction definition."""

from __future__ import annotations

from qa_report_generator.application.service_definitions.base import ServiceDefinition

from .post_processing import build_post_processed_runs
from .prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
    build_verification_user_prompt,
)
from .schema import SymbolstreeserviceExtractedMetrics

SERVICE_DEFINITION = ServiceDefinition(
    name="symbolstreeservice",
    schema_model=SymbolstreeserviceExtractedMetrics,
    remove_keys=frozenset({"setup_data", "root_group"}),
    extraction_system_prompt=EXTRACTION_SYSTEM_PROMPT,
    verification_system_prompt=VERIFICATION_SYSTEM_PROMPT,
    build_extraction_user_prompt=build_extraction_user_prompt,
    build_verification_user_prompt=build_verification_user_prompt,
    post_process_extracted=build_post_processed_runs,
)
