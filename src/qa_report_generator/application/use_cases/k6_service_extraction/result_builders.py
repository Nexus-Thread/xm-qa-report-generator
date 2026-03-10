"""Result building helpers for k6 extraction use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6ServiceExtractionRun

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
                "metrics": scenario.metrics,
            },
        )
        for scenario in parsed_report.scenarios
    ]
    return K6ServiceExtractionResult(
        service=parsed_report.service,
        mode="generic",
        runs=runs,
    )
