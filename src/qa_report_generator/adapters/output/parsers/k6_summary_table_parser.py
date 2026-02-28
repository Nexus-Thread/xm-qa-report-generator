"""Parser for k6 summary JSON files into summary rows."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from qa_report_generator.application.dtos import K6SummaryRow
from qa_report_generator.application.service_definitions.megatron.mapping import pick_metric, pick_primary_scenario_name
from qa_report_generator.domain.exceptions import ConfigurationError

if TYPE_CHECKING:
    from pathlib import Path


class K6SummaryTableParser:
    """Parse multiple k6 JSON files into tabular summary rows."""

    def parse(self, *, report_files: list[Path]) -> list[K6SummaryRow]:
        """Parse each report file into one summary row."""
        rows: list[K6SummaryRow] = []
        for report_path in report_files:
            source = self._load_json(report_path)
            scenario_name = pick_primary_scenario_name(source)
            source.get("execScenarios", {}).get(scenario_name, {})

            duration_metric = pick_metric(source, "http_req_duration", scenario_name)
            checks_metric = source.get("metrics", {}).get("checks", {})
            iterations_metric = source.get("metrics", {}).get("iterations", {})

            rows.append(
                K6SummaryRow(
                    report_file=report_path.name,
                    scenario=scenario_name,
                    request_rate=float(self._get_nested(iterations_metric, "values", "rate", default=0.0)),
                    iterations=int(self._get_nested(iterations_metric, "values", "count", default=0)),
                    p95_duration_ms=float(self._get_nested(duration_metric, "values", "p(95)", default=0.0)),
                    p99_duration_ms=float(self._get_nested(duration_metric, "values", "p(99)", default=0.0)),
                    checks_rate=float(self._get_nested(checks_metric, "values", "rate", default=0.0)),
                )
            )
        return rows

    def _load_json(self, path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            msg = f"Invalid k6 JSON report: {path}"
            raise ConfigurationError(msg, suggestion="Validate k6 artifact JSON format") from err

    def _get_nested(self, source: dict[str, Any], *keys: str, default: float) -> float | int:
        current: Any = source
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]
        if isinstance(current, (int, float)):
            return current
        return default
