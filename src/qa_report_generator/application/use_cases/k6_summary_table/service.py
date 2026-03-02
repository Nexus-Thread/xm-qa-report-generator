"""Use case for parsing consolidated k6 summary rows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import K6SummaryTableResult

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.ports.output import K6SummaryTableParserPort


class K6SummaryTableService:
    """Parse consolidated k6 summary rows from report files."""

    def __init__(self, *, parser: K6SummaryTableParserPort) -> None:
        """Store parser dependency."""
        self._parser = parser

    def generate_k6_summary_table(self, *, report_files: list[Path]) -> K6SummaryTableResult:
        """Parse k6 reports and return consolidated rows."""
        rows = self._parser.parse(report_files=report_files)
        return K6SummaryTableResult(rows=rows)
