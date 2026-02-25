"""Narrative generation adapters.

Narrative adapters are split into performance (k6) and functional (pytest) submodules.
"""

# Performance narrative adapters (k6)
from qa_report_generator.adapters.output.narrative.performance import (
    NarrativeAdapter as PerformanceNarrativeAdapter,
    NarrativeAdapterConfig as PerformanceNarrativeAdapterConfig,
)

# Functional narrative adapters (pytest)
from qa_report_generator.adapters.output.narrative.functional import (
    NarrativeAdapter as FunctionalNarrativeAdapter,
    NarrativeAdapterConfig as FunctionalNarrativeAdapterConfig,
)

# Default to functional for backward compatibility
NarrativeAdapter = FunctionalNarrativeAdapter
NarrativeAdapterConfig = FunctionalNarrativeAdapterConfig

__all__ = [
    "NarrativeAdapter",
    "NarrativeAdapterConfig",
    "PerformanceNarrativeAdapter",
    "PerformanceNarrativeAdapterConfig",
    "FunctionalNarrativeAdapter",
    "FunctionalNarrativeAdapterConfig",
]
