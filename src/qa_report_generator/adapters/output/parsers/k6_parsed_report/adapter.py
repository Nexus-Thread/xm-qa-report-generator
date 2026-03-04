"""Parser for k6 JSON files into parsed report domain models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.ports.output import K6ParsedReportParserPort
from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario

from .file_loader import load_json_report
from .mapping import extract_scenarios, remove_top_level_keys
from .validation import validate_report

if TYPE_CHECKING:
    from pathlib import Path


class K6ParsedReportParser(K6ParsedReportParserPort):
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
            source = load_json_report(report_file)
            sanitized_source = remove_top_level_keys(source, remove_keys=effective_remove_keys)
            validated_report = validate_report(sanitized_source)
            scenarios.extend(
                extract_scenarios(
                    sanitized_source=sanitized_source,
                    validated_report=validated_report,
                    source_report_file=report_file,
                )
            )

        return K6ParsedReport(service=service, scenarios=scenarios)
