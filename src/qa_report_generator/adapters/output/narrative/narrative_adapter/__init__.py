"""Narrative generation adapter using an OpenAI-compatible LLM."""

from qa_report_generator.adapters.output.narrative.narrative_adapter.adapter import NarrativeAdapter
from qa_report_generator.adapters.output.narrative.narrative_adapter.config import LLMAdapterConfig

__all__ = ["LLMAdapterConfig", "NarrativeAdapter"]
