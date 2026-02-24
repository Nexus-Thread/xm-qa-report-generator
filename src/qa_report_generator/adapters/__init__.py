"""Adapters layer - Infrastructure implementations.

This module contains adapters that connect the application core to external systems
and services, following the hexagonal architecture pattern:

- **Input adapters** (driving): Entry points that trigger application logic (e.g., CLI)
- **Output adapters** (driven): Implementations of ports for external services
  (e.g., LLM, file parsers, report writers)

All adapters implement interfaces (ports) defined in the application layer,
ensuring clean separation between business logic and infrastructure concerns.
"""

from qa_report_generator.adapters.input.cli_adapter import CliAdapter
from qa_report_generator.adapters.output.narrative import NarrativeAdapter
from qa_report_generator.adapters.output.parsers import PytestJsonParser
from qa_report_generator.adapters.output.persistence.markdown_writer import MarkdownReportWriter

__all__ = [
    "CliAdapter",
    "MarkdownReportWriter",
    "NarrativeAdapter",
    "PytestJsonParser",
]
