"""Orchestrator for deterministic service-specific k6 metric extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator_performance.application.dtos import K6ServiceExtractionResult
from qa_report_generator_performance.application.exceptions import (
    ConfigurationError,
)
from qa_report_generator_performance.application.ports.input import ExtractK6ServiceMetricsUseCase
from qa_report_generator_performance.application.service_definitions import get_service_definition

from .config import K6ServiceExtractionDebugConfig, K6ServiceExtractionRuntimeConfig
from .service_specific_extraction import run_service_specific_pipeline

if TYPE_CHECKING:
    from pathlib import Path

    from qa_report_generator_performance.application.dtos import (
        K6ServiceExtractionRun,
        LlmUsageSummary,
    )
    from qa_report_generator_performance.application.ports.output import K6ParsedReportParserPort, StructuredLlmPort
    from qa_report_generator_performance.application.service_definitions.shared.base import ServiceDefinition
    from qa_report_generator_performance.domain.analytics import K6ParsedReport


class K6ServiceExtractionService(ExtractK6ServiceMetricsUseCase):
    """Extract deterministic structured metrics for one service from a k6 summary JSON."""

    def __init__(
        self,
        *,
        llm: StructuredLlmPort,
        parser: K6ParsedReportParserPort,
        runtime_config: K6ServiceExtractionRuntimeConfig | None = None,
        debug_config: K6ServiceExtractionDebugConfig | None = None,
    ) -> None:
        """Store adapter dependencies."""
        resolved_runtime_config = runtime_config or K6ServiceExtractionRuntimeConfig()

        if resolved_runtime_config.max_parallel_scenarios < 1:
            msg = "max_parallel_scenarios must be greater than or equal to 1"
            raise ValueError(msg)
        if resolved_runtime_config.max_verification_attempts < 1:
            msg = "max_verification_attempts must be greater than or equal to 1"
            raise ValueError(msg)

        self._llm = llm
        self._parser = parser
        self._llm_usage_summary_provider = resolved_runtime_config.llm_usage_summary_provider
        self._max_parallel_scenarios = resolved_runtime_config.max_parallel_scenarios
        self._max_verification_attempts = resolved_runtime_config.max_verification_attempts
        self._debug_config = debug_config or K6ServiceExtractionDebugConfig()

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Parse reports, run the relevant pipeline, and return the final result."""
        if self._llm_usage_summary_provider is not None:
            self._llm_usage_summary_provider.reset()

        if not report_paths:
            msg = "No report files provided for extraction"
            raise ConfigurationError(msg, suggestion="Pass one or more k6 JSON reports")

        definition = get_service_definition(service)

        # Step 1: parse the input JSON files into a normalized report model.
        parsed_report = self._parse_report(
            service=service,
            report_paths=report_paths,
            definition=definition,
        )

        pipeline_artifacts = run_service_specific_pipeline(
            llm=self._llm,
            parsed_report=parsed_report,
            definition=definition,
            max_parallel_scenarios=self._max_parallel_scenarios,
            max_verification_attempts=self._max_verification_attempts,
        )
        self._write_result_snapshots(
            extracted_runs=pipeline_artifacts.extracted_runs,
            post_processed_runs=pipeline_artifacts.post_processed_runs,
            summary_result=pipeline_artifacts.summary_result,
        )
        return K6ServiceExtractionResult(
            service=pipeline_artifacts.summary_result.service,
            runs=pipeline_artifacts.summary_result.runs,
            overall_summary=pipeline_artifacts.summary_result.overall_summary,
            scenario_summaries=pipeline_artifacts.summary_result.scenario_summaries,
            llm_usage_summary=self._build_llm_usage_summary(),
        )

    def _build_llm_usage_summary(self) -> LlmUsageSummary | None:
        """Return aggregated LLM usage when a provider is configured."""
        if self._llm_usage_summary_provider is None:
            return None
        return self._llm_usage_summary_provider.build_summary()

    def _parse_report(
        self,
        *,
        service: str,
        report_paths: list[Path],
        definition: ServiceDefinition,
    ) -> K6ParsedReport:
        """Parse source reports with service-specific key filtering."""
        return self._parser.parse(
            service=service,
            report_files=report_paths,
            remove_keys=definition.remove_keys,
        )

    def _write_result_snapshots(
        self,
        *,
        extracted_runs: list[K6ServiceExtractionRun],
        post_processed_runs: list[K6ServiceExtractionRun],
        summary_result: K6ServiceExtractionResult,
    ) -> None:
        """Persist standardized snapshots for extraction debugging."""
        self._write_model_snapshot(label="extracted_runs", payload=extracted_runs)
        self._write_model_snapshot(label="post_processed_runs", payload=post_processed_runs)
        self._write_model_snapshot(label="summary_output", payload=summary_result.to_summary_payload())

    def _write_model_snapshot(self, *, label: str, payload: object) -> None:
        """Persist a model snapshot when model debug JSON output is enabled."""
        if not self._debug_config.model_debug_json_enabled or self._debug_config.model_debug_json_writer is None:
            return
        self._debug_config.model_debug_json_writer.write_json(label=label, payload=payload)
