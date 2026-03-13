"""Unit tests for k6 extraction DTO helpers."""

from __future__ import annotations

from qa_report_generator_performance.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
)
from qa_report_generator_performance.domain.analytics import (
    K6OverallExecutiveSummary,
    K6ScenarioExecutiveSummary,
    K6ThresholdSummary,
)


def test_k6_service_extraction_run_normalizes_provenance_and_copies_payload() -> None:
    """Run DTO coerces provenance to tuple and detaches the payload copy."""
    payload = {
        "service": "megatron",
        "threshold_statuses": {},
    }
    run = K6ServiceExtractionRun(
        source_report_files=("report.json",),
        extracted=payload,
    )
    payload["service"] = "mutated"

    assert run.source_report_files == ("report.json",)
    assert run.extracted == {
        "service": "megatron",
        "threshold_statuses": {},
    }


def test_k6_service_extraction_result_to_summary_payload_returns_summary_only() -> None:
    """Result DTO serializes the adapter-facing summary payload without runs."""
    result = K6ServiceExtractionResult(
        service="megatron",
        runs=[
            K6ServiceExtractionRun(
                source_report_files=("report.json",),
                extracted={"service": "megatron"},
            )
        ],
        overall_summary=K6OverallExecutiveSummary(
            status="pass",
            total_scenarios=1,
            passed_scenarios=1,
            failed_scenarios=0,
            unknown_scenarios=0,
            scenarios_requiring_attention=(),
            executive_summary="All 1 scenarios passed their evaluated thresholds.",
        ),
        scenario_summaries=[
            K6ScenarioExecutiveSummary(
                scenario_name="megatron-load",
                env_name="staging",
                source_report_files=("report.json",),
                status="pass",
                executor="constant-arrival-rate",
                rate=10.0,
                duration="1m",
                pre_allocated_vus=10,
                max_vus=20,
                threshold_results=(
                    K6ThresholdSummary(
                        metric_key="checks",
                        expression="rate>0.99",
                        status="pass",
                    ),
                ),
                executive_note="Scenario megatron-load met all evaluated thresholds.",
            )
        ],
    )

    payload = result.to_summary_payload()

    assert payload["service"] == "megatron"
    assert "runs" not in payload
    assert payload["scenario_summaries"] == [
        {
            "scenario_name": "megatron-load",
            "env_name": "staging",
            "source_report_files": ("report.json",),
            "status": "pass",
            "executor": "constant-arrival-rate",
            "rate": 10.0,
            "duration": "1m",
            "pre_allocated_vus": 10,
            "max_vus": 20,
            "threshold_results": [
                {
                    "metric_key": "checks",
                    "expression": "rate>0.99",
                    "status": "pass",
                }
            ],
            "executive_note": "Scenario megatron-load met all evaluated thresholds.",
        }
    ]
