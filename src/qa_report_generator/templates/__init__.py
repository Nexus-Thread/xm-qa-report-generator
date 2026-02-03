"""Prompt template management for LLM-based test report generation.

This module provides tools for loading and managing prompt templates used by
LLMs to generate narrative sections in test reports.
"""

from qa_report_generator.templates.prompt_loader import PromptLoader, PromptTemplate

__all__ = ["PromptLoader", "PromptTemplate"]
