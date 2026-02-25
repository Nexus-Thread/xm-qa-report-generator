"""Narrative generation adapter using an OpenAI-compatible LLM transport."""

from qa_report_generator.adapters.output.narrative.narrative_adapter.adapter import NarrativeAdapter
from qa_report_generator.adapters.output.narrative.narrative_adapter.config import NarrativeAdapterConfig

__all__ = ["NarrativeAdapter", "NarrativeAdapterConfig"]
