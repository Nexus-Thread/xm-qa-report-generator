"""Functional persistence adapters (pytest)."""

from qa_report_generator.adapters.output.persistence.functional.cache import FileReportCache
from qa_report_generator.adapters.output.persistence.functional.markdown_writer import MarkdownReportWriter

__all__ = ["FileReportCache", "MarkdownReportWriter"]
