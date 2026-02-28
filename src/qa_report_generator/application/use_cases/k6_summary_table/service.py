"""Use case for generating consolidated k6 summary markdown tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import K6SummaryTableResult

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.ports.output import K6SummaryTableParserPort, K6SummaryTableWriterPort


class K6SummaryTableService:
    """Generate a consolidated k6 summary table from report files."""

    def __init__(self, *, parser: K6SummaryTableParserPort, writer: K6SummaryTableWriterPort) -> None:
        """Store parser and writer dependencies."""
        self._parser = parser
        self._writer = writer

    def generate_k6_summary_table(self, *, report_files: list[Path], output_path: Path) -> K6SummaryTableResult:
        """Parse k6 reports and write consolidated markdown summary."""
        rows = self._parser.parse(report_files=report_files)
        written_path = self._writer.write(rows=rows, output_path=output_path)
        return K6SummaryTableResult(output_path=written_path, rows_count=len(rows))
