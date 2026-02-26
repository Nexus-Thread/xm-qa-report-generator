"""Performance test parsing adapters (k6)."""

from qa_report_generator.adapters.output.parsers.performance.parser import K6JsonParser
from qa_report_generator.adapters.output.parsers.performance.summary_parser import K6SummaryTableParser

__all__ = ["K6JsonParser", "K6SummaryTableParser"]
