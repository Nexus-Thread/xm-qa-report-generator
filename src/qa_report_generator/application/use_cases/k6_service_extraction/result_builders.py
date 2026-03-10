"""Result building helpers for k6 extraction use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6ServiceExtractionRun
from qa_report_generator.domain.analytics import (
    build_overall_executive_summary,
    build_scenario_executive_summary,
    build_threshold_summaries_from_source_payload,
)

if TYPE_CHECKING:
    from qa_report_generator.domain.analytics import K6ParsedReport


def build_generic_result(*, parsed_report: K6ParsedReport) -> K6ServiceExtractionResult:
    """Build generic parsed output when no service definition exists."""
    runs = [
        K6ServiceExtractionRun(
            source_report_files=[scenario.source_report_file],
            extracted={
                "service": parsed_report.service,
                "scenario": {
                    "name": scenario.name,
                    "env_name": scenario.env_name,
                    "executor": scenario.executor,
                    "rate": scenario.rate,
                    "duration": scenario.duration,
                    "pre_allocated_vus": scenario.pre_allocated_vus,
                    "max_vus": scenario.max_vus,
                },
                "test_run_duration_ms": scenario.test_run_duration_ms,
                "thresholds": scenario.thresholds,
                "threshold_results": [
                    {
                        "metric_key": threshold.metric_key,
                        "expression": threshold.expression,
                        "status": threshold.status,
                    }
                    for threshold in build_threshold_summaries_from_source_payload(
                        source_payload=scenario.raw_payload,
                    )
                ],
                "metrics": scenario.metrics,
            },
        )
        for scenario in parsed_report.scenarios
    ]
    scenario_summaries = [
        build_scenario_executive_summary(
            run_payload=run.extracted,
            source_report_files=run.source_report_files,
        )
        for run in runs
    ]
    return K6ServiceExtractionResult(
        service=parsed_report.service,
        mode="generic",
        runs=runs,
        overall_summary=build_overall_executive_summary(scenario_summaries=scenario_summaries),
        scenario_summaries=scenario_summaries,
    )
