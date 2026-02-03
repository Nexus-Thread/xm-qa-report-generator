"""LLM adapter module for narrative generation."""

from qa_report_generator.adapters.output.narrative.llm_adapter.adapter import LLMAdapter
from qa_report_generator.adapters.output.narrative.llm_adapter.config import LLMAdapterConfig

# Internal modules (types, validators, retry_handler) are not exported
# to maintain a clean public API
__all__ = ["LLMAdapter", "LLMAdapterConfig"]
