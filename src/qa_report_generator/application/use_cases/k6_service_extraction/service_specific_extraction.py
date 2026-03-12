"""Service-specific extraction flow for parsed k6 reports."""

from __future__ import annotations

import logging
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
)
from qa_report_generator.domain.analytics import (
    analyze_overall_scenarios,
    analyze_scenario_run,
    build_overall_executive_summary,
    build_scenario_executive_summary,
)
from qa_report_generator.domain.exceptions import ReportingError

from .scenario_extraction import ExtractedRunModel, extract_verified_run_model
from .thresholds import build_threshold_summaries_from_source_payload

if TYPE_CHECKING:
    from pydantic import BaseModel

    from qa_report_generator.application.ports.output import StructuredLlmPort
    from qa_report_generator.application.service_definitions.shared.base import ServiceDefinition
    from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ServiceSpecificPipelineArtifacts:
    """Structured outputs produced by the service-specific pipeline after parsing."""

    extracted_runs: list[K6ServiceExtractionRun]
    post_processed_runs: list[K6ServiceExtractionRun]
    summary_result: K6ServiceExtractionResult


@dataclass(frozen=True, slots=True)
class _IndexedExtractedRunModel:
    """One extracted run model paired with its original scenario index."""

    index: int
    run_model: ExtractedRunModel


def run_service_specific_pipeline(
    *,
    llm: StructuredLlmPort,
    parsed_report: K6ParsedReport,
    definition: ServiceDefinition,
    max_parallel_scenarios: int = 1,
) -> ServiceSpecificPipelineArtifacts:
    """Run extract -> post-process -> summary for an already parsed report."""
    schema = definition.dump_schema()

    # Step 2: extract one validated run model per parsed scenario.
    extracted_run_models = _extract_run_models(
        llm=llm,
        scenarios=parsed_report.scenarios,
        definition=definition,
        schema=schema,
        max_parallel_scenarios=max_parallel_scenarios,
    )
    extracted_runs = [
        K6ServiceExtractionRun.from_extracted_payload(
            source_report_files=(run_model.source_report_file,),
            extracted=run_model.extracted.model_dump(by_alias=True),
            threshold_results=build_threshold_summaries_from_source_payload(
                source_payload=run_model.source_payload,
            ),
        )
        for run_model in extracted_run_models
    ]

    # Step 3: apply optional service-specific post-processing to extracted runs.
    post_processed_runs = _post_process_runs(
        definition=definition,
        fallback_runs=extracted_runs,
        extracted_models=[run_model.extracted for run_model in extracted_run_models],
    )

    # Step 4: analyze prepared runs, then project summaries from those analyses.
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
        mode="service_specific",
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
    schema: dict[str, object],
    max_parallel_scenarios: int,
) -> list[ExtractedRunModel]:
    """Extract scenario payloads sequentially or in parallel while preserving order."""
    if max_parallel_scenarios <= 1 or len(scenarios) <= 1:
        return [
            extract_verified_run_model(
                llm=llm,
                scenario=scenario,
                definition=definition,
                schema=schema,
            )
            for scenario in scenarios
        ]

    indexed_results: list[ExtractedRunModel | None] = [None] * len(scenarios)
    with ThreadPoolExecutor(max_workers=max_parallel_scenarios) as executor:
        futures = {
            executor.submit(
                _extract_indexed_run_model,
                llm=llm,
                index=index,
                scenario=scenario,
                definition=definition,
                schema=schema,
            ): scenario
            for index, scenario in enumerate(scenarios)
        }

        for future in as_completed(futures):
            scenario = futures[future]
            try:
                indexed_run_model = future.result()
            except ReportingError as err:
                _cancel_pending_futures(futures=futures)
                raise _build_scenario_processing_error(error=err, scenario=scenario) from err
            indexed_results[indexed_run_model.index] = indexed_run_model.run_model

    return [run_model for run_model in indexed_results if run_model is not None]


def _extract_indexed_run_model(
    *,
    llm: StructuredLlmPort,
    index: int,
    scenario: K6Scenario,
    definition: ServiceDefinition,
    schema: dict[str, object],
) -> _IndexedExtractedRunModel:
    """Extract one scenario and retain its original position for stable ordering."""
    return _IndexedExtractedRunModel(
        index=index,
        run_model=extract_verified_run_model(
            llm=llm,
            scenario=scenario,
            definition=definition,
            schema=schema,
        ),
    )


def _cancel_pending_futures(*, futures: dict[Future[_IndexedExtractedRunModel], K6Scenario]) -> None:
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
    fallback_runs: list[K6ServiceExtractionRun],
    extracted_models: list[BaseModel],
) -> list[K6ServiceExtractionRun]:
    """Build final runs after optional post-processing."""
    if definition.post_process_extracted is None:
        return fallback_runs
    return definition.post_process_extracted(extracted_models)
