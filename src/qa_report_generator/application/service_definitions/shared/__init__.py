"""Shared building blocks for service definitions."""

from .base import ServiceDefinition
from .prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
    build_verification_user_prompt,
)
from .registry import ServiceDefinitionRegistry

__all__ = [
    "EXTRACTION_SYSTEM_PROMPT",
    "VERIFICATION_SYSTEM_PROMPT",
    "ServiceDefinition",
    "ServiceDefinitionRegistry",
    "build_extraction_user_prompt",
    "build_verification_user_prompt",
]
