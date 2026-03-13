"""Shared building blocks for service definitions."""

from .base import ServiceDefinition
from .merge_strategies import (
    SchemaMergeBuckets,
    derive_merge_buckets,
    merge_counter_metric_field,
    merge_optional_counter_metric_field,
    merge_rate_metric_field,
    merge_trend_metric_field,
)
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
    "SchemaMergeBuckets",
    "ServiceDefinition",
    "ServiceDefinitionRegistry",
    "build_extraction_user_prompt",
    "build_verification_user_prompt",
    "derive_merge_buckets",
    "merge_counter_metric_field",
    "merge_optional_counter_metric_field",
    "merge_rate_metric_field",
    "merge_trend_metric_field",
]
