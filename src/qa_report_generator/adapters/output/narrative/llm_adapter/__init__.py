"""LLM adapter module for narrative generation."""

from qa_report_generator.adapters.output.narrative.llm_adapter.adapter import LLMAdapter
from qa_report_generator.adapters.output.narrative.llm_adapter.config import LLMAdapterConfig

# Internal helper modules are not exported to keep a clean public API.
__all__ = ["LLMAdapter", "LLMAdapterConfig"]
