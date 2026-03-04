"""Parser for k6 JSON files into parsed report domain models."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario
from qa_report_generator.domain.exceptions import ConfigurationError

from .raw_schema import K6RawSummary

if TYPE_CHECKING:
    from pathlib import Path


class K6ParsedReportParser:
    """Parse k6 JSON files into scenario-centric parsed report models."""

    def parse(
        self,
        *,
        service: str,
        report_files: list[Path],
        remove_keys: frozenset[str] | None = None,
    ) -> K6ParsedReport:
        """Parse report files and return a parsed report with scenario entries."""
        effective_remove_keys = remove_keys if remove_keys is not None else frozenset()
        scenarios: list[K6Scenario] = []

        for report_file in report_files:
            source = self._load_json(report_file)
            scenarios.extend(
                self._extract_scenarios(
                    source=source,
                    source_report_file=report_file,
                    remove_keys=effective_remove_keys,
                )
            )

        return K6ParsedReport(service=service, scenarios=scenarios)

    def _load_json(self, path: Path) -> dict[str, Any]:
        try:
            with path.open(encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as err:
            msg = f"Invalid k6 JSON report: {path}"
            raise ConfigurationError(msg, suggestion="Validate k6 artifact JSON format") from err
        except OSError as err:
            msg = f"Unable to read k6 JSON report: {path}"
            raise ConfigurationError(msg, suggestion="Ensure report file exists and is readable") from err

    def _extract_scenarios(
        self,
        *,
        source: dict[str, Any],
        source_report_file: Path,
        remove_keys: frozenset[str],
    ) -> list[K6Scenario]:
        sanitized_source = self._remove_top_level_keys(source, remove_keys=remove_keys)
        validated_report = self._validate_report(sanitized_source)
        exec_scenarios = validated_report.exec_scenarios
        if not exec_scenarios:
            msg = "Missing execScenarios object"
            raise ConfigurationError(msg, suggestion="Ensure report includes execScenarios")

        metrics = self._normalize_metrics(sanitized_source.get("metrics"))
        thresholds = validated_report.exec_thresholds
        run_duration = validated_report.state.test_run_duration_ms if validated_report.state else 0.0

        parsed_scenarios: list[K6Scenario] = []
        for scenario_name, raw_config in exec_scenarios.items():
            tags = raw_config.tags if isinstance(raw_config.tags, dict) else {}

            parsed_scenarios.append(
                K6Scenario(
                    source_report_file=source_report_file.name,
                    name=str(scenario_name),
                    env_name=self._extract_env_name(tags=tags),
                    executor=raw_config.executor,
                    rate=raw_config.rate if raw_config.rate is not None else 0.0,
                    duration=raw_config.duration if raw_config.duration is not None else "",
                    pre_allocated_vus=(raw_config.pre_allocated_vus if raw_config.pre_allocated_vus is not None else 0),
                    max_vus=raw_config.max_vus if raw_config.max_vus is not None else 0,
                    test_run_duration_ms=run_duration,
                    thresholds=deepcopy(thresholds),
                    metrics=deepcopy(metrics),
                    raw_payload=deepcopy(sanitized_source),
                )
            )

        return parsed_scenarios

    def _remove_top_level_keys(self, source: dict[str, Any], *, remove_keys: frozenset[str]) -> dict[str, Any]:
        if not remove_keys:
            return dict(source)
        return {key: value for key, value in source.items() if key not in remove_keys}

    def _validate_report(self, source: dict[str, Any]) -> K6RawSummary:
        try:
            return K6RawSummary.model_validate(source)
        except ValidationError as err:
            msg = "Invalid k6 report schema"
            raise ConfigurationError(msg, suggestion=str(err)) from err

    def _normalize_metrics(self, value: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(value, dict):
            return {}
        return {
            metric_name: metric_payload for metric_name, metric_payload in value.items() if isinstance(metric_name, str) and isinstance(metric_payload, dict)
        }

    def _extract_env_name(self, *, tags: dict[str, Any]) -> str | None:
        tagged_env_name = tags.get("env_name")
        if isinstance(tagged_env_name, str) and tagged_env_name:
            return tagged_env_name

        return None
