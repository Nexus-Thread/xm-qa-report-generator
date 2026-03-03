"""Parser adapter exports."""

from .k6_parsed_report import K6ParsedReportParser
from .k6_summary_table_parser import K6SummaryTableParser

__all__ = ["K6ParsedReportParser", "K6SummaryTableParser"]
