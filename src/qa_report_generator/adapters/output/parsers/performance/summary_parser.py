"""Parser that extracts one consolidated k6 summary row per report file."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from qa_report_generator.application.ports.output import K6SummaryParser
from qa_report_generator.domain.exceptions import ParseFileNotFoundError, ParseInvalidFormatError, ParseInvalidJsonError
from qa_report_generator.domain.models import K6SummaryRow

if TYPE_CHECKING:
    from pathlib import Path

_DURATION_PATTERN = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")


class K6SummaryTableParser(K6SummaryParser):
    """Extract a consolidated summary row from a k6 summary JSON file."""

    def parse_summary_row(self, filepath: Path) -> K6SummaryRow:
        """Parse a single k6 summary report into one table row."""
        payload = self._read_json(filepath)
        scenario_name, scenario_config = self._extract_scenario(payload)

        target_load_rps = int(scenario_config.get("rate") or 0)
        duration_seconds = self._extract_duration_seconds(payload, scenario_config)
        if duration_seconds <= 0:
            msg = f"Scenario duration is missing or zero in {filepath}"
            raise ParseInvalidFormatError(msg, suggestion="Ensure execScenarios.<scenario>.duration is set")

        metrics: dict[str, Any] = payload.get("metrics", {})
        iterations = int(((metrics.get("iterations") or {}).get("values") or {}).get("count", 0))
        achieved_rps = (iterations / duration_seconds) if duration_seconds > 0 else 0.0

        thresholds = self._extract_thresholds(payload.get("execThresholds", {}), scenario_name)
        latency_values = self._extract_latency(metrics, scenario_name)
        error_rate_percent = self._extract_error_rate_percent(metrics, scenario_name)
        outcome_passed = self._extract_outcome(metrics, scenario_name)

        return K6SummaryRow(
            service=self._service_from_scenario(scenario_name),
            scenario=scenario_name,
            target_load_rps=target_load_rps,
            duration_seconds=duration_seconds,
            thresholds=thresholds,
            iterations=iterations,
            achieved_rps=achieved_rps,
            latency_med_ms=float(latency_values.get("med", 0.0)),
            latency_p95_ms=float(latency_values.get("p(95)", 0.0)),
            latency_p99_ms=float(latency_values.get("p(99)", 0.0)),
            latency_max_ms=float(latency_values.get("max", 0.0)),
            error_rate_percent=error_rate_percent,
            outcome_passed=outcome_passed,
        )

    def _read_json(self, filepath: Path) -> dict[str, Any]:
        try:
            return json.loads(filepath.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            msg = f"Report file not found: {filepath}"
            raise ParseFileNotFoundError(msg, suggestion="Check the reports directory path") from exc
        except json.JSONDecodeError as exc:
            msg = f"Invalid JSON in report file: {filepath} (line {exc.lineno}, column {exc.colno})"
            raise ParseInvalidJsonError(msg, suggestion="Ensure k6 finished and wrote valid JSON") from exc

    def _extract_scenario(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        scenarios = payload.get("execScenarios") or {}
        if not scenarios:
            msg = "Missing execScenarios in k6 summary report"
            raise ParseInvalidFormatError(msg, suggestion="Use k6 --summary-export output")

        scenario_name = next(iter(scenarios.keys()))
        scenario_config = scenarios.get(scenario_name)
        if not isinstance(scenario_config, dict):
            msg = f"Invalid scenario configuration for {scenario_name}"
            raise ParseInvalidFormatError(msg, suggestion="Ensure execScenarios values are objects")

        return scenario_name, scenario_config

    def _extract_duration_seconds(self, payload: dict[str, Any], scenario_config: dict[str, Any]) -> int:
        raw_duration = scenario_config.get("duration")
        if isinstance(raw_duration, str):
            parsed = self._parse_duration(raw_duration)
            if parsed > 0:
                return parsed

        state = payload.get("state") or {}
        duration_ms = state.get("testRunDurationMs")
        if duration_ms is not None:
            return int(float(duration_ms) / 1000)
        return 0

    def _parse_duration(self, raw_duration: str) -> int:
        match = _DURATION_PATTERN.fullmatch(raw_duration)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    def _extract_thresholds(self, exec_thresholds: dict[str, Any], scenario_name: str) -> list[str]:
        expressions: list[str] = []
        for metric_name, threshold_expressions in exec_thresholds.items():
            if scenario_name in metric_name and isinstance(threshold_expressions, list):
                expressions.extend([str(expr) for expr in threshold_expressions])
        return sorted(expressions, key=self._threshold_sort_key)

    def _extract_latency(self, metrics: dict[str, Any], scenario_name: str) -> dict[str, Any]:
        latency_metric = metrics.get(f"http_req_duration{{test_name:{scenario_name}}}") or {}
        return latency_metric.get("values") or {}

    def _extract_error_rate_percent(self, metrics: dict[str, Any], scenario_name: str) -> float:
        error_metric = metrics.get(f"http_req_failed{{test_name:{scenario_name}}}") or {}
        error_values = error_metric.get("values") or {}
        return float(error_values.get("rate", 0.0)) * 100.0

    def _extract_outcome(self, metrics: dict[str, Any], scenario_name: str) -> bool:
        statuses: list[bool] = []
        for metric_name, metric_data in metrics.items():
            if scenario_name not in metric_name or not isinstance(metric_data, dict):
                continue
            thresholds = metric_data.get("thresholds") or {}
            statuses.extend(
                bool(threshold_data.get("ok", False))
                for threshold_data in thresholds.values()
                if isinstance(threshold_data, dict)
            )
        return bool(statuses) and all(statuses)

    def _service_from_scenario(self, scenario_name: str) -> str:
        match = re.match(r"([a-z]+)", scenario_name)
        return match.group(1).upper() if match else "N/A"

    def _threshold_sort_key(self, expression: str) -> tuple[int, str]:
        if expression.startswith("p(95)<"):
            return (0, expression)
        if expression.startswith("p(99)<"):
            return (1, expression)
        if expression.startswith("rate<"):
            return (2, expression)
        return (99, expression)
