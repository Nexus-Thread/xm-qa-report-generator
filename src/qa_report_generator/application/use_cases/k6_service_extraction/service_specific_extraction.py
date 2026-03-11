"""Service-specific extraction flow for parsed k6 reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
)
from qa_report_generator.domain.analytics import (
    build_overall_executive_summary,
    build_scenario_executive_summary,
)

from .scenario_extraction import extract_verified_run_model
from .thresholds import build_threshold_summaries_from_source_payload

if TYPE_CHECKING:
    from pydantic import BaseModel

    from qa_report_generator.application.ports.output import StructuredLlmPort
    from qa_report_generator.application.service_definitions.base import ServiceDefinition
    from qa_report_generator.domain.analytics import K6ParsedReport


@dataclass(frozen=True, slots=True)
class ServiceSpecificExtractionArtifacts:
    """Structured outputs produced by the service-specific extraction flow."""

    extraction_runs: list[K6ServiceExtractionRun]
    final_runs: list[K6ServiceExtractionRun]
    result: K6ServiceExtractionResult


def extract_service_specific_result(
    *,
    llm: StructuredLlmPort,
    parsed_report: K6ParsedReport,
    definition: ServiceDefinition,
) -> ServiceSpecificExtractionArtifacts:
    """Run service-specific extraction flow for parsed scenarios."""
    schema = definition.dump_schema()
    extracted_run_models = [
        extract_verified_run_model(
            llm=llm,
            scenario=scenario,
            definition=definition,
            schema=schema,
        )
        for scenario in parsed_report.scenarios
    ]
    extraction_runs = [
        K6ServiceExtractionRun.from_extracted_payload(
            source_report_files=(run_model.source_report_file,),
            extracted=run_model.extracted.model_dump(by_alias=True),
            threshold_results=build_threshold_summaries_from_source_payload(
                source_payload=run_model.source_payload,
            ),
        )
        for run_model in extracted_run_models
    ]
    final_runs = _post_process_runs(
        definition=definition,
        fallback_runs=extraction_runs,
        extracted_models=[run_model.extracted for run_model in extracted_run_models],
    )
    scenario_summaries = [
        build_scenario_executive_summary(
            run_payload=run.extracted,
            source_report_files=run.source_report_files,
        )
        for run in final_runs
    ]

    result = K6ServiceExtractionResult(
        service=parsed_report.service,
        mode="service_specific",
        runs=final_runs,
        overall_summary=build_overall_executive_summary(scenario_summaries=scenario_summaries),
        scenario_summaries=scenario_summaries,
    )
    return ServiceSpecificExtractionArtifacts(
        extraction_runs=extraction_runs,
        final_runs=final_runs,
        result=result,
    )


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
