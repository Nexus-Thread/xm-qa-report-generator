"""Performance persistence adapters (k6)."""

from qa_report_generator.adapters.output.persistence.performance.cache import FileReportCache
from qa_report_generator.adapters.output.persistence.performance.markdown_writer import MarkdownReportWriter

__all__ = ["FileReportCache", "MarkdownReportWriter"]
