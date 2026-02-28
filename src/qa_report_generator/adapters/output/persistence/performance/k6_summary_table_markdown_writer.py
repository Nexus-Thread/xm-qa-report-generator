"""Writer adapter for consolidated k6 summary markdown output."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.dtos import K6SummaryRow


class K6SummaryTableMarkdownWriter:
    """Render k6 summary rows into a markdown table file."""

    def write(self, *, rows: list[K6SummaryRow], output_path: Path) -> Path:
        """Write markdown table to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "| report_file | scenario | request_rate | iterations | p95_duration_ms | p99_duration_ms | checks_rate |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        lines.extend(
            (
                "| "
                f"{row.report_file} | {row.scenario} | {row.request_rate:.6f} | {row.iterations} | "
                f"{row.p95_duration_ms:.6f} | {row.p99_duration_ms:.6f} | {row.checks_rate:.6f} |"
            )
            for row in rows
        )
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_path
