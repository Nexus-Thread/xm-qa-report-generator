"""Output adapters - Implementations of external service interfaces.

Output adapters (also called "driven" adapters) implement ports defined by the
application core. They handle interactions with external systems and services
while keeping the business logic independent of infrastructure details.

Categories:
- **narrative/**: LLM-based narrative generation adapters
- **parsers/**: Report parsing adapters (e.g., pytest JSON parser)
- **persistence/**: Report writing/storage adapters (e.g., markdown writer)
"""

from qa_report_generator.adapters.output.narrative import LLMAdapter
from qa_report_generator.adapters.output.parsers import PytestJsonParser
from qa_report_generator.adapters.output.persistence import MarkdownReportWriter

__all__ = [
    "LLMAdapter",
    "MarkdownReportWriter",
    "PytestJsonParser",
]
