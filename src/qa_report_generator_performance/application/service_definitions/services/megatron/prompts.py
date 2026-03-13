"""Megatron prompt exports."""

from qa_report_generator_performance.application.service_definitions.shared.prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
    build_verification_user_prompt,
)

__all__ = [
    "EXTRACTION_SYSTEM_PROMPT",
    "VERIFICATION_SYSTEM_PROMPT",
    "build_extraction_user_prompt",
    "build_verification_user_prompt",
]
