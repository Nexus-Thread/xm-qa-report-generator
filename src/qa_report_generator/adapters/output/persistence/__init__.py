"""Report persistence adapters for saving generated reports.

These adapters handle writing and storing generated reports in various formats
and locations (e.g., file system, cloud storage, databases).

Currently available:
- **MarkdownReportWriter**: Writes test reports as markdown files
- **FileReportCache**: Caches parsed report facts for regeneration
"""

from qa_report_generator.adapters.output.persistence.cache import FileReportCache
from qa_report_generator.adapters.output.persistence.markdown_writer import MarkdownReportWriter

__all__ = [
    "FileReportCache",
    "MarkdownReportWriter",
]
