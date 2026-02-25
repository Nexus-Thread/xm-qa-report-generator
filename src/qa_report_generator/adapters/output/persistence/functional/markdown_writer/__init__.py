"""Markdown report writer module.

This module provides markdown report generation capabilities,
split into focused submodules for maintainability.
"""

from qa_report_generator.adapters.output.persistence.markdown_writer.adapter import MarkdownReportWriter

__all__ = [
    "MarkdownReportWriter",
]
