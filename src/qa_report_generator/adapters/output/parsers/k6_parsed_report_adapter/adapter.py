"""Parser for k6 JSON files into parsed report domain models."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import ValidationError

from qa_report_generator.application.exceptions import ConfigurationError
from qa_report_generator.application.ports.output import K6ParsedReportParserPort
from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario

from .mapper import build_scenarios
from .schema import K6RawSummary

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Any


class K6ParsedReportParser(K6ParsedReportParserPort):
    """Parse k6 JSON files into scenario-centric parsed report models."""

    def parse(
        self,
        *,
        service: str,
        report_files: Sequence[Path],
        remove_keys: frozenset[str] = frozenset(),
    ) -> K6ParsedReport:
        """Parse report files and return a parsed report with scenario entries."""
        if not report_files:
            msg = "At least one k6 JSON report file is required"
            raise ConfigurationError(msg, suggestion="Provide one or more generated k6 JSON report files")

        scenarios: list[K6Scenario] = []
        for report_file in report_files:
            scenarios.extend(
                self._parse_report_file(
                    report_file=report_file,
                    remove_keys=remove_keys,
                )
            )

        return K6ParsedReport(service=service, scenarios=tuple(scenarios))

    def _parse_report_file(
        self,
        *,
        report_file: Path,
        remove_keys: frozenset[str],
    ) -> list[K6Scenario]:
        """Load, validate, and map one report file into parsed scenarios."""
        source = _load_json_report(report_file)
        sanitized_source = _remove_top_level_keys(source, remove_keys=remove_keys)
        validated_report = _validate_report(sanitized_source)
        return build_scenarios(
            report=validated_report,
            source_payload=sanitized_source,
            source_report_file=report_file.name,
        )


def _load_json_report(path: Path) -> dict[str, Any]:
    """Load and decode a k6 JSON report file."""
    try:
        with path.open(encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as err:
        msg = f"Invalid k6 JSON report: {path}"
        raise ConfigurationError(msg, suggestion="Validate k6 artifact JSON format") from err
    except OSError as err:
        msg = f"Unable to read k6 JSON report: {path}"
        raise ConfigurationError(msg, suggestion="Ensure report file exists and is readable") from err

    if not isinstance(payload, dict):
        msg = f"Invalid k6 JSON report root object: {path}"
        raise ConfigurationError(msg, suggestion="Ensure k6 report JSON uses an object at the top level")

    return payload


def _remove_top_level_keys(source: dict[str, Any], *, remove_keys: frozenset[str]) -> dict[str, Any]:
    """Return payload copy with selected top-level keys removed."""
    if not remove_keys:
        return dict(source)
    return {key: value for key, value in source.items() if key not in remove_keys}


def _validate_report(source: dict[str, Any]) -> K6RawSummary:
    """Validate raw report payload against the internal schema."""
    try:
        return K6RawSummary.model_validate(source)
    except ValidationError as err:
        msg = "Invalid k6 report schema"
        raise ConfigurationError(msg, suggestion=str(err)) from err
