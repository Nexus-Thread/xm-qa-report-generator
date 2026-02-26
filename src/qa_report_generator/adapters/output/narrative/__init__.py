"""Narrative generation adapters.

Narrative adapters are split into performance (k6) and functional (pytest) submodules.
"""

# Performance narrative adapters (k6)
# Functional narrative adapters (pytest)
from qa_report_generator.adapters.output.narrative.functional import (
    NarrativeAdapter as FunctionalNarrativeAdapter,
)
from qa_report_generator.adapters.output.narrative.functional import (
    NarrativeAdapterConfig as FunctionalNarrativeAdapterConfig,
)
from qa_report_generator.adapters.output.narrative.performance import (
    NarrativeAdapter as PerformanceNarrativeAdapter,
)
from qa_report_generator.adapters.output.narrative.performance import (
    NarrativeAdapterConfig as PerformanceNarrativeAdapterConfig,
)

# Default to functional for backward compatibility
NarrativeAdapter = FunctionalNarrativeAdapter
NarrativeAdapterConfig = FunctionalNarrativeAdapterConfig

__all__ = [
    "FunctionalNarrativeAdapter",
    "FunctionalNarrativeAdapterConfig",
    "NarrativeAdapter",
    "NarrativeAdapterConfig",
    "PerformanceNarrativeAdapter",
    "PerformanceNarrativeAdapterConfig",
]
