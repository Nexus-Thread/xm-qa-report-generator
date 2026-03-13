"""Service-specific extraction flow for parsed k6 reports."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_report_generator_performance.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
)
from qa_report_generator_performance.application.service_definitions.shared.base import PreparedExtractionRun
from qa_report_generator_performance.domain.analytics import (
    analyze_overall_scenarios,
    analyze_scenario_run,
    build_overall_executive_summary,
    build_scenario_executive_summary,
)
from qa_report_generator_performance.domain.exceptions import ReportingError

from .scenario_extraction import ExtractedRunModel, extract_verified_run_model
from .source_payload import collect_threshold_status_map

if TYPE_CHECKING:
    from qa_report_generator_performance.application.ports.output import StructuredLlmPort
    from qa_report_generator_performance.application.service_definitions.shared.base import ServiceDefinition
    from qa_report_generator_performance.domain.analytics import K6ParsedReport, K6Scenario

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ServiceSpecificPipelineArtifacts:
    """Structured outputs produced by the service-specific pipeline after parsing."""

    extracted_runs: list[K6ServiceExtractionRun]
    post_processed_runs: list[K6ServiceExtractionRun]
    summary_result: K6ServiceExtractionResult


@dataclass(frozen=True, slots=True)
class _ExtractionExecutionConfig:
    """Execution settings shared by sequential and parallel extraction paths."""

    schema: dict[str, object]
    max_verification_attempts: int


def run_service_specific_pipeline(
    *,
    llm: StructuredLlmPort,
    parsed_report: K6ParsedReport,
    definition: ServiceDefinition,
    max_parallel_scenarios: int = 1,
    max_verification_attempts: int = 3,
) -> ServiceSpecificPipelineArtifacts:
    """Run extract -> post-process -> summary for an already parsed report."""
    schema = definition.dump_schema()
    extraction_config = _ExtractionExecutionConfig(
        schema=schema,
        max_verification_attempts=max_verification_attempts,
    )

    # Step 2: extract one validated run model per parsed scenario.
    extracted_run_models = _extract_run_models(
        llm=llm,
        scenarios=parsed_report.scenarios,
        definition=definition,
        extraction_config=extraction_config,
        max_parallel_scenarios=max_parallel_scenarios,
    )
    prepared_runs = [_build_prepared_run(run_model=run_model, definition=definition) for run_model in extracted_run_models]
    extracted_runs = [_to_extraction_run(prepared_run=prepared_run) for prepared_run in prepared_runs]

    # Step 2b: apply optional service-specific post-processing before DTO conversion.
    post_processed_prepared_runs = _post_process_runs(
        definition=definition,
        fallback_runs=prepared_runs,
    )
    post_processed_runs = [_to_extraction_run(prepared_run=prepared_run) for prepared_run in post_processed_prepared_runs]

    # Step 3: analyze prepared runs, then project summaries from those analyses.
    scenario_analyses = [
        analyze_scenario_run(
            run_payload=run.extracted,
            source_report_files=run.source_report_files,
        )
        for run in post_processed_runs
    ]
    overall_analysis = analyze_overall_scenarios(scenario_analyses=scenario_analyses)
    scenario_summaries = [build_scenario_executive_summary(analysis=analysis) for analysis in scenario_analyses]

    summary_result = K6ServiceExtractionResult(
        service=parsed_report.service,
        runs=post_processed_runs,
        overall_summary=build_overall_executive_summary(analysis=overall_analysis),
        scenario_summaries=scenario_summaries,
    )
    return ServiceSpecificPipelineArtifacts(
        extracted_runs=extracted_runs,
        post_processed_runs=post_processed_runs,
        summary_result=summary_result,
    )


def _extract_run_models(
    *,
    llm: StructuredLlmPort,
    scenarios: tuple[K6Scenario, ...],
    definition: ServiceDefinition,
    extraction_config: _ExtractionExecutionConfig,
    max_parallel_scenarios: int,
) -> list[ExtractedRunModel]:
    """Extract scenario payloads sequentially or in parallel while preserving order."""
    if max_parallel_scenarios <= 1 or len(scenarios) <= 1:
        return [
            extract_verified_run_model(
                llm=llm,
                scenario=scenario,
                definition=definition,
                schema=extraction_config.schema,
                max_verification_attempts=extraction_config.max_verification_attempts,
            )
            for scenario in scenarios
        ]

    indexed_results: list[ExtractedRunModel | None] = [None] * len(scenarios)
    with ThreadPoolExecutor(max_workers=max_parallel_scenarios) as executor:
        futures = {
            executor.submit(
                extract_verified_run_model,
                llm=llm,
                scenario=scenario,
                definition=definition,
                schema=extraction_config.schema,
                max_verification_attempts=extraction_config.max_verification_attempts,
            ): (index, scenario)
            for index, scenario in enumerate(scenarios)
        }

        for future in as_completed(futures):
            index, scenario = futures[future]
            try:
                indexed_run_model = future.result()
            except ReportingError as err:
                _cancel_pending_futures(futures=futures)
                raise _build_scenario_processing_error(error=err, scenario=scenario) from err
            indexed_results[index] = indexed_run_model

    return [run_model for run_model in indexed_results if run_model is not None]


def _cancel_pending_futures(*, futures: dict[Future[ExtractedRunModel], tuple[int, K6Scenario]]) -> None:
    """Cancel futures that have not started yet after the first failure."""
    for future in futures:
        future.cancel()


def _build_scenario_processing_error(*, error: ReportingError, scenario: K6Scenario) -> ReportingError:
    """Augment a reporting error with scenario context for clearer failures."""
    message = f"Scenario processing failed for {scenario.name} ({scenario.source_report_file}): {error}"
    LOGGER.error(
        "Scenario processing failed",
        extra={
            "component": "service_specific_extraction",
            "scenario_name": scenario.name,
            "source_report_file": scenario.source_report_file,
            "error_type": type(error).__name__,
        },
    )
    return type(error)(message, suggestion=error.suggestion)


def _post_process_runs(
    *,
    definition: ServiceDefinition,
    fallback_runs: list[PreparedExtractionRun],
) -> list[PreparedExtractionRun]:
    """Build final prepared runs after optional post-processing."""
    if definition.post_process_extracted is None:
        return fallback_runs
    return definition.post_process_extracted(fallback_runs)


def _build_prepared_run(
    *,
    run_model: ExtractedRunModel,
    definition: ServiceDefinition,
) -> PreparedExtractionRun:
    """Build one prepared typed extraction result before output conversion."""
    enriched_payload = run_model.extracted.model_dump(by_alias=True)
    enriched_payload["threshold_statuses"] = collect_threshold_status_map(
        metric_payloads=_as_metrics_payload(run_model.source_payload),
    )
    return PreparedExtractionRun(
        source_report_files=(run_model.source_report_file,),
        extracted=definition.schema_model.model_validate(enriched_payload),
    )


def _to_extraction_run(*, prepared_run: PreparedExtractionRun) -> K6ServiceExtractionRun:
    """Convert one prepared typed run into the output extraction DTO."""
    extracted_payload = prepared_run.extracted.model_dump(
        by_alias=True,
        exclude={"report_file"},
    )
    if "threshold_results" in extracted_payload:
        msg = "Prepared extraction payload unexpectedly contains threshold_results before analysis"
        raise TypeError(msg)
    return K6ServiceExtractionRun(
        source_report_files=prepared_run.source_report_files,
        extracted=extracted_payload,
    )


def _as_metrics_payload(source_payload: dict[str, object]) -> dict[str, object]:
    """Return raw metric payload mapping or an empty fallback."""
    metrics = source_payload.get("metrics")
    return metrics if isinstance(metrics, dict) else {}
