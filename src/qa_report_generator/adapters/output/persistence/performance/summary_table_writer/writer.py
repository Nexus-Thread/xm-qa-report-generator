"""Write consolidated k6 summary rows into a markdown table file."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.ports.output import K6SummaryWriter
from qa_report_generator.domain.exceptions import PersistenceError

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.domain.models import K6SummaryRow


class K6SummaryTableMarkdownWriter(K6SummaryWriter):
    """Write markdown table for consolidated k6 summary rows."""

    def write_summary_table(self, rows: list[K6SummaryRow], output_path: Path) -> Path:
        """Write consolidated markdown table and return output path."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(self._render_table(rows), encoding="utf-8")
        except OSError as exc:
            msg = f"Failed to write k6 summary table: {output_path}"
            raise PersistenceError(msg, suggestion="Check output path permissions") from exc
        return output_path

    def _render_table(self, rows: list[K6SummaryRow]) -> str:
        headers = [
            "Service",
            "Scenario",
            "Duration",
            "Target load (rps)",
            "Achieved (steady-state, rps)",
            "Outcome",
            "Error rate",
            "Latency metrics (ms)",
            "Target threshold(s)",
            "Comment",
        ]

        ordered_rows = sorted(rows, key=lambda row: row.scenario.lower())

        lines = ["# Summary", ""]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        lines.extend(
            "| "
            + " | ".join(
                [
                    row.service,
                    row.scenario,
                    self._format_duration(row.duration_seconds),
                    str(row.target_load_rps),
                    self._format_achieved(row.achieved_rps),
                    "✅ Passed" if row.outcome_passed else "❌ Failed",
                    f"{row.error_rate_percent:.1f}%",
                    self._format_latency(row),
                    self._format_thresholds(row.thresholds),
                    self._format_comment(row.outcome_passed),
                ]
            )
            + " |"
            for row in ordered_rows
        )

        lines.append("")
        return "\n".join(lines)

    def _format_duration(self, duration_seconds: int) -> str:
        minutes, seconds = divmod(duration_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}h{minutes}m{seconds}s"
        if seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m{seconds}s"

    def _format_thresholds(self, thresholds: dict[str, list[str]]) -> str:
        if not thresholds:
            return "N/A"

        rendered_groups: list[str] = []
        for metric_name in sorted(thresholds):
            expressions = thresholds[metric_name]
            if not expressions:
                rendered_groups.append(f"{metric_name}: N/A")
                continue

            rendered_expressions = ", ".join(self._format_threshold(expression) for expression in sorted(expressions))
            rendered_groups.append(f"{metric_name}: {rendered_expressions}")

        return "; ".join(rendered_groups)

    def _format_threshold(self, expression: str) -> str:
        if expression.startswith("p(95)<"):
            return f"p95 < {expression.split('<', 1)[1]}ms"
        if expression.startswith("p(99)<"):
            return f"p99 < {expression.split('<', 1)[1]}ms"
        if expression.startswith("rate<"):
            rate_percent = float(expression.split("<", 1)[1]) * 100.0
            rendered = f"{rate_percent:.0f}" if rate_percent.is_integer() else f"{rate_percent:.1f}"
            return f"rate < {rendered}%"
        return expression

    def _format_achieved(self, achieved_rps: float) -> str:
        return f"{achieved_rps:.2f}"

    def _format_latency(self, row: K6SummaryRow) -> str:
        if not row.latency_metrics_ms:
            return "N/A"

        parts = [f"{metric_name}={self._format_latency_value(value)}ms" for metric_name, value in sorted(row.latency_metrics_ms.items())]
        return ", ".join(parts)

    def _format_latency_value(self, value: float) -> str:
        rounded = round(value)
        if abs(value - rounded) < 0.0001:
            return str(rounded)
        return f"{value:.1f}"

    def _format_comment(self, outcome_passed: bool) -> str:
        if outcome_passed:
            return "Throughput sustained; latency gates pass; no HTTP failures observed."
        return "Throughput sustained and reliable, but tail latency breaches p95/p99 thresholds."
