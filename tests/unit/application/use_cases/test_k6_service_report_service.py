"""Unit tests for k6 service report orchestration use case."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_report_generator.application.dtos import K6ServiceExtractionResult, K6ServiceExtractionRun
from qa_report_generator.application.use_cases.k6_service_report import K6ServiceReportService
from qa_report_generator.domain.analytics import K6ParsedReport, K6Scenario

if TYPE_CHECKING:
    from pathlib import Path


class SpyParsedReportParser:
    """Spy parser capturing parse arguments for assertions."""

    def __init__(self, *, parsed_report: K6ParsedReport) -> None:
        """Store deterministic parser result."""
        self._parsed_report = parsed_report
        self.calls: list[tuple[str, list[Path], frozenset[str] | None]] = []

    def parse(
        self,
        *,
        service: str,
        report_files: list[Path],
        remove_keys: frozenset[str] | None = None,
    ) -> K6ParsedReport:
        """Record parse call and return deterministic parsed report."""
        self.calls.append((service, report_files, remove_keys))
        return self._parsed_report


class SpyExtractionUseCase:
    """Spy extraction use case capturing extraction call args."""

    def __init__(self, *, result: K6ServiceExtractionResult) -> None:
        """Store deterministic extraction result."""
        self._result = result
        self.calls: list[tuple[str, list[Path]]] = []

    def extract(self, *, service: str, report_paths: list[Path]) -> K6ServiceExtractionResult:
        """Record extraction call and return deterministic payload."""
        self.calls.append((service, report_paths))
        return self._result


def test_generate_service_report_combines_parsed_and_extracted_payloads(tmp_path: Path) -> None:
    """Service report orchestration returns parsed and extracted payloads together."""
    report_path = tmp_path / "report.json"
    report_path.write_text("{}", encoding="utf-8")

    parsed_report = K6ParsedReport(
        service="megatron",
        scenarios=[
            K6Scenario(
                source_report_file="report.json",
                name="megatron-load",
                env_name="staging",
                executor="constant-arrival-rate",
                rate=10,
                duration="1m",
                pre_allocated_vus=5,
                max_vus=10,
                test_run_duration_ms=60_000,
                thresholds={"http_req_duration": ["p(95)<300"]},
                metrics={"checks": {"values": {"rate": 1.0}}},
                raw_payload={"execScenarios": {}},
            )
        ],
    )
    extraction_result = K6ServiceExtractionResult(
        service="megatron",
        extracted_runs=[
            K6ServiceExtractionRun(
                report_file="report.json",
                extracted={"service": "megatron"},
            )
        ],
    )
    parser = SpyParsedReportParser(parsed_report=parsed_report)
    extraction_use_case = SpyExtractionUseCase(result=extraction_result)
    service = K6ServiceReportService(
        parser=parser,
        extraction_use_case=extraction_use_case,
    )

    result = service.generate_service_report(
        service="megatron",
        report_paths=[report_path],
    )

    assert result.service == "megatron"
    assert result.parsed_report == parsed_report
    assert result.extraction == extraction_result
    assert parser.calls[0][0] == "megatron"
    assert parser.calls[0][1] == [report_path]
    assert parser.calls[0][2] == frozenset({"setup_data", "root_group"})
    assert extraction_use_case.calls == [("megatron", [report_path])]
