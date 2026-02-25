"""Report persistence adapters for saving generated reports.

These adapters handle writing and storing generated reports in various formats
and locations (e.g., file system, cloud storage, databases).

Persistence adapters are split into performance (k6) and functional (pytest) submodules.

Currently available:
- **MarkdownReportWriter**: Writes test reports as markdown files
- **FileReportCache**: Caches parsed report facts for regeneration
"""

# Performance persistence adapters (k6)
from qa_report_generator.adapters.output.persistence.performance import (
    FileReportCache as PerformanceFileReportCache,
    MarkdownReportWriter as PerformanceMarkdownReportWriter,
)

# Functional persistence adapters (pytest)
from qa_report_generator.adapters.output.persistence.functional import (
    FileReportCache as FunctionalFileReportCache,
    MarkdownReportWriter as FunctionalMarkdownReportWriter,
)

# Default to functional for backward compatibility
FileReportCache = FunctionalFileReportCache
MarkdownReportWriter = FunctionalMarkdownReportWriter

__all__ = [
    "FileReportCache",
    "MarkdownReportWriter",
    "PerformanceFileReportCache",
    "PerformanceMarkdownReportWriter",
    "FunctionalFileReportCache",
    "FunctionalMarkdownReportWriter",
]
