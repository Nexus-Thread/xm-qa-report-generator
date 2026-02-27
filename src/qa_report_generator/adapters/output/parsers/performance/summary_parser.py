"""Parser that extracts one consolidated k6 summary row per report file."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from qa_report_generator.application.ports.output import K6SummaryParser
from qa_report_generator.domain.exceptions import (
    ParseFileNotFoundError,
    ParseInvalidFormatError,
    ParseInvalidJsonError,
)
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
        latency_metrics_ms = self._extract_latency_metrics_ms(metrics, scenario_name)
        error_rate_percent = self._extract_error_rate_percent(metrics, scenario_name)
        outcome_passed = self._extract_outcome(metrics, scenario_name)
        observed_vus_current, observed_vus_peak = self._extract_observed_vus(metrics)

        return K6SummaryRow(
            service=self._service_from_scenario(scenario_name),
            scenario=scenario_name,
            executor=self._extract_executor(scenario_config),
            time_unit=self._extract_time_unit(scenario_config),
            pre_allocated_vus=self._extract_non_negative_int(scenario_config.get("preAllocatedVUs")),
            max_vus=self._extract_non_negative_int(scenario_config.get("maxVUs")),
            observed_vus_current=observed_vus_current,
            observed_vus_peak=observed_vus_peak,
            target_load_rps=target_load_rps,
            duration_seconds=duration_seconds,
            thresholds=thresholds,
            iterations=iterations,
            achieved_rps=achieved_rps,
            latency_metrics_ms=latency_metrics_ms,
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

    def _extract_executor(self, scenario_config: dict[str, Any]) -> str:
        raw_executor = scenario_config.get("executor")
        if isinstance(raw_executor, str) and raw_executor.strip():
            return raw_executor.strip()
        return "unknown"

    def _extract_time_unit(self, scenario_config: dict[str, Any]) -> str | None:
        raw_time_unit = scenario_config.get("timeUnit")
        if not isinstance(raw_time_unit, str):
            return None
        normalized_time_unit = raw_time_unit.strip()
        return normalized_time_unit or None

    def _parse_duration(self, raw_duration: str) -> int:
        match = _DURATION_PATTERN.fullmatch(raw_duration)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    def _extract_thresholds(
        self,
        exec_thresholds: dict[str, Any],
        scenario_name: str,
    ) -> dict[str, list[str]]:
        threshold_map: dict[str, list[str]] = {}
        for metric_name, threshold_expressions in exec_thresholds.items():
            if not self._metric_matches_scenario(metric_name, scenario_name):
                continue
            if not isinstance(threshold_expressions, list):
                continue

            normalized_metric_name = self._normalize_metric_name(metric_name)
            threshold_map.setdefault(normalized_metric_name, []).extend(str(expression) for expression in threshold_expressions)

        return {metric_name: sorted(set(expressions)) for metric_name, expressions in sorted(threshold_map.items())}

    def _extract_latency_metrics_ms(
        self,
        metrics: dict[str, Any],
        scenario_name: str,
    ) -> dict[str, float]:
        raw_values = self._extract_metric_values(metrics, "http_req_duration", scenario_name)
        parsed_values: dict[str, float] = {}
        for metric_name, raw_value in raw_values.items():
            if not isinstance(metric_name, str) or not metric_name:
                continue
            numeric_value = self._coerce_float(raw_value)
            if numeric_value < 0.0:
                continue
            parsed_values[metric_name] = numeric_value

        return {metric_name: parsed_values[metric_name] for metric_name in sorted(parsed_values)}

    def _extract_error_rate_percent(self, metrics: dict[str, Any], scenario_name: str) -> float:
        error_values = self._extract_metric_values(metrics, "http_req_failed", scenario_name)
        return self._coerce_float(error_values.get("rate")) * 100.0

    def _extract_observed_vus(self, metrics: dict[str, Any]) -> tuple[int | None, int | None]:
        vus_values = self._extract_metric_values(metrics, "vus", scenario_name="")
        vus_max_values = self._extract_metric_values(metrics, "vus_max", scenario_name="")

        observed_vus_current = self._extract_non_negative_int(vus_values.get("value"))
        observed_vus_peak = self._extract_non_negative_int(vus_values.get("max"))
        if observed_vus_peak is not None:
            return observed_vus_current, observed_vus_peak

        fallback_peak = self._extract_non_negative_int(vus_max_values.get("value"))
        if fallback_peak is not None:
            return observed_vus_current, fallback_peak

        return observed_vus_current, self._extract_non_negative_int(vus_max_values.get("max"))

    def _extract_outcome(self, metrics: dict[str, Any], scenario_name: str) -> bool:
        statuses: list[bool] = []
        for metric_name, metric_data in metrics.items():
            if not isinstance(metric_data, dict):
                continue
            if not self._metric_matches_scenario(metric_name, scenario_name):
                continue
            thresholds = metric_data.get("thresholds") or {}
            statuses.extend(bool(threshold_data.get("ok", False)) for threshold_data in thresholds.values() if isinstance(threshold_data, dict))
        return bool(statuses) and all(statuses)

    def _extract_metric_values(
        self,
        metrics: dict[str, Any],
        metric_name: str,
        scenario_name: str,
    ) -> dict[str, Any]:
        for key in self._candidate_metric_keys(metric_name, scenario_name):
            metric_data = metrics.get(key)
            if not isinstance(metric_data, dict):
                continue
            values = metric_data.get("values")
            if isinstance(values, dict):
                return values
        return {}

    def _candidate_metric_keys(self, metric_name: str, scenario_name: str) -> list[str]:
        return [
            f"{metric_name}{{test_name:{scenario_name}}}",
            metric_name,
        ]

    def _metric_matches_scenario(self, metric_name: str, scenario_name: str) -> bool:
        if "test_name:" not in metric_name:
            return True
        return f"test_name:{scenario_name}" in metric_name

    def _normalize_metric_name(self, metric_name: str) -> str:
        return metric_name.split("{", maxsplit=1)[0]

    def _coerce_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _extract_non_negative_int(self, value: Any) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None

    def _service_from_scenario(self, scenario_name: str) -> str:
        match = re.match(r"([a-z]+)", scenario_name)
        return match.group(1).upper() if match else "N/A"
