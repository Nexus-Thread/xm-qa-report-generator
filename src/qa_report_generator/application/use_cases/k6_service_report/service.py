"""Use case orchestrating parsed k6 report and deterministic extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import K6ServiceReportResult
from qa_report_generator.application.service_definitions import get_service_definition

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.ports.input import ExtractK6ServiceMetricsUseCase
    from qa_report_generator.application.ports.output import K6ParsedReportParserPort


class K6ServiceReportService:
    """Generate service report payload by combining parsing and extraction."""

    def __init__(
        self,
        *,
        parser: K6ParsedReportParserPort,
        extraction_use_case: ExtractK6ServiceMetricsUseCase,
    ) -> None:
        """Store parser and extraction dependencies."""
        self._parser = parser
        self._extraction_use_case = extraction_use_case

    def generate_service_report(self, *, service: str, report_paths: list[Path]) -> K6ServiceReportResult:
        """Generate combined parsed and extracted service report result."""
        definition = get_service_definition(service)
        parsed_report = self._parser.parse(
            service=service,
            report_files=report_paths,
            remove_keys=definition.remove_keys,
        )
        extraction = self._extraction_use_case.extract(
            service=service,
            report_paths=report_paths,
        )

        return K6ServiceReportResult(
            service=service,
            parsed_report=parsed_report,
            extraction=extraction,
        )
