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
            "Load expected (rps)",
            "Load actual (rps)",
            "Error rate expected (%)",
            "Error rate actual (%)",
            "p95 expected (ms)",
            "p95 actual (ms)",
            "p99 expected (ms)",
            "p99 actual (ms)",
            "Outcome",
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
                    self._format_optional_percent(
                        self._extract_threshold_percent(
                            row.thresholds,
                            metric_name="http_req_failed",
                            prefix="rate<",
                            multiplier=100.0,
                        )
                    ),
                    self._format_optional_percent(row.error_rate_percent),
                    self._format_optional_latency(
                        self._extract_threshold_percent(
                            row.thresholds,
                            metric_name="http_req_duration",
                            prefix="p(95)<",
                        )
                    ),
                    self._format_optional_latency(row.latency_metrics_ms.get("p(95)")),
                    self._format_optional_latency(
                        self._extract_threshold_percent(
                            row.thresholds,
                            metric_name="http_req_duration",
                            prefix="p(99)<",
                        )
                    ),
                    self._format_optional_latency(row.latency_metrics_ms.get("p(99)")),
                    "✅ Passed" if row.outcome_passed else "❌ Failed",
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

    def _format_achieved(self, achieved_rps: float) -> str:
        return f"{achieved_rps:.2f}"

    def _extract_threshold_percent(
        self,
        thresholds: dict[str, list[str]],
        *,
        metric_name: str,
        prefix: str,
        multiplier: float = 1.0,
    ) -> float | None:
        for expression in thresholds.get(metric_name, []):
            if not expression.startswith(prefix):
                continue
            try:
                return float(expression.split("<", 1)[1]) * multiplier
            except ValueError:
                return None
        return None

    def _format_optional_percent(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return f"{value:.1f}"

    def _format_optional_latency(self, value: float | None) -> str:
        if value is None:
            return "N/A"
        return self._format_latency_value(value)

    def _format_latency_value(self, value: float) -> str:
        rounded = round(value)
        if abs(value - rounded) < 0.0001:
            return str(rounded)
        return f"{value:.1f}"

    def _format_comment(self, outcome_passed: bool) -> str:
        if outcome_passed:
            return "Throughput sustained; latency gates pass; no HTTP failures observed."
        return "Throughput sustained and reliable, but tail latency breaches p95/p99 thresholds."
