"""Unit tests for k6 summary markdown writer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.adapters.output.persistence.performance import K6SummaryTableMarkdownWriter
from qa_report_generator.application.dtos import K6SummaryRow

if TYPE_CHECKING:
    from pathlib import Path


def test_write_outputs_markdown_table(tmp_path: Path) -> None:
    """Writer renders expected markdown header and row content."""
    writer = K6SummaryTableMarkdownWriter()
    output_path = tmp_path / "out" / "summary.md"

    rows = [
        K6SummaryRow(
            report_file="report.json",
            scenario="megatron-load",
            request_rate=4.2,
            iterations=42,
            p95_duration_ms=150.0,
            p99_duration_ms=200.0,
            checks_rate=1.0,
        )
    ]

    writer.write(rows=rows, output_path=output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "| report_file | scenario | request_rate | iterations | p95_duration_ms | p99_duration_ms | checks_rate |" in content
    assert "| report.json | megatron-load | 4.200000 | 42 | 150.000000 | 200.000000 | 1.000000 |" in content
