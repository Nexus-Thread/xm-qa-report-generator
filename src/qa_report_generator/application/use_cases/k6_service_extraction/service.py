"""Orchestrator for deterministic service-specific k6 metric extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.exceptions import (
    ConfigurationError,
)
from qa_report_generator.application.ports.input import ExtractK6ServiceMetricsUseCase
from qa_report_generator.application.service_definitions import get_optional_service_definition

from .config import K6ServiceExtractionDebugConfig
from .result_builders import build_generic_result
from .service_specific_extraction import extract_service_specific_result

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator.application.dtos import (
        K6ServiceExtractionResult,
        K6ServiceExtractionRun,
    )
    from qa_report_generator.application.ports.output import K6ParsedReportParserPort, StructuredLlmPort
    from qa_report_generator.application.service_definitions.base import ServiceDefinition
    from qa_report_generator.domain.analytics import K6ParsedReport


class K6ServiceExtractionService(ExtractK6ServiceMetricsUseCase):
    """Extract deterministic structured metrics for one service from a k6 summary JSON."""

    def __init__(
        self,
        *,
        llm: StructuredLlmPort,
        parser: K6ParsedReportParserPort,
        debug_config: K6ServiceExtractionDebugConfig | None = None,
    ) -> None:
        """Store adapter dependencies."""
        self._llm = llm
        self._parser = parser
        self._debug_config = debug_config or K6ServiceExtractionDebugConfig()

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Parse reports, dispatch flow, and return validated payloads."""
        if not report_paths:
            msg = "No report files provided for extraction"
            raise ConfigurationError(msg, suggestion="Pass one or more k6 JSON reports")

        definition = get_optional_service_definition(service)
        parsed_report = self._parse_report(
            service=service,
            report_paths=report_paths,
            definition=definition,
        )

        if definition is None:
            result = build_generic_result(parsed_report=parsed_report)
            self._write_result_snapshots(
                extraction_runs=result.runs,
                post_processed_runs=result.runs,
                result=result,
            )
            return result

        artifacts = extract_service_specific_result(
            llm=self._llm,
            parsed_report=parsed_report,
            definition=definition,
        )
        self._write_result_snapshots(
            extraction_runs=artifacts.extraction_runs,
            post_processed_runs=artifacts.final_runs,
            result=artifacts.result,
        )
        return artifacts.result

    def _parse_report(
        self,
        *,
        service: str,
        report_paths: list[Path],
        definition: ServiceDefinition | None,
    ) -> K6ParsedReport:
        """Parse source reports with service-specific key filtering."""
        remove_keys = definition.remove_keys if definition is not None else frozenset()
        return self._parser.parse(
            service=service,
            report_files=report_paths,
            remove_keys=remove_keys,
        )

    def _write_result_snapshots(
        self,
        *,
        extraction_runs: list[K6ServiceExtractionRun],
        post_processed_runs: list[K6ServiceExtractionRun],
        result: K6ServiceExtractionResult,
    ) -> None:
        """Persist standardized snapshots for extraction debugging."""
        self._write_model_snapshot(label="extraction_runs", payload=extraction_runs)
        self._write_model_snapshot(label="post_processed_runs", payload=post_processed_runs)
        self._write_model_snapshot(label="summary_output", payload=result.to_summary_payload())

    def _write_model_snapshot(self, *, label: str, payload: object) -> None:
        """Persist a model snapshot when model debug JSON output is enabled."""
        if not self._debug_config.model_debug_json_enabled or self._debug_config.model_debug_json_writer is None:
            return
        self._debug_config.model_debug_json_writer.write_json(label=label, payload=payload)
