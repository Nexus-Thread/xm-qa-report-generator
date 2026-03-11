"""Unit tests for k6 extraction DTO helpers."""

from __future__ import annotations

from qa_report_generator.application.dtos import (
    K6ServiceExtractionResult,
    K6ServiceExtractionRun,
    normalize_k6_extracted_payload,
)
from qa_report_generator.domain.analytics import (
    K6OverallExecutiveSummary,
    K6ScenarioExecutiveSummary,
    K6ThresholdSummary,
)


def test_normalize_k6_extracted_payload_removes_internal_fields() -> None:
    """Payload normalization strips extraction-only fields from a copied payload."""
    payload = {
        "report_file": "report.json",
        "service": "megatron",
    }

    normalized = normalize_k6_extracted_payload(payload)

    assert normalized == {"service": "megatron"}
    assert payload == {
        "report_file": "report.json",
        "service": "megatron",
    }


def test_k6_service_extraction_run_normalizes_provenance_and_payload() -> None:
    """Run DTO coerces provenance to tuple and strips extraction-only payload fields."""
    run = K6ServiceExtractionRun(
        source_report_files=("report.json",),
        extracted={
            "report_file": "report.json",
            "service": "megatron",
        },
    )

    assert run.source_report_files == ("report.json",)
    assert run.extracted == {"service": "megatron"}


def test_k6_service_extraction_run_from_extracted_payload_serializes_thresholds() -> None:
    """Run factory attaches serialized threshold results while normalizing payload."""
    run = K6ServiceExtractionRun.from_extracted_payload(
        source_report_files=["report.json"],
        extracted={
            "report_file": "report.json",
            "service": "megatron",
        },
        threshold_results=[
            K6ThresholdSummary(
                metric_key="checks",
                expression="rate>0.99",
                status="pass",
            )
        ],
    )

    assert run.source_report_files == ("report.json",)
    assert run.extracted == {
        "service": "megatron",
        "threshold_results": [
            {
                "metric_key": "checks",
                "expression": "rate>0.99",
                "status": "pass",
            }
        ],
    }


def test_k6_service_extraction_result_to_summary_payload_returns_summary_only() -> None:
    """Result DTO serializes the adapter-facing summary payload without runs."""
    result = K6ServiceExtractionResult(
        service="megatron",
        mode="service_specific",
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
    assert payload["mode"] == "service_specific"
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
