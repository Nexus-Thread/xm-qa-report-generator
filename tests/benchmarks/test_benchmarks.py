"""Benchmark tests for key reporting workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

pytest.importorskip("pytest_benchmark")

from qa_report_generator.adapters.output.parsers import PytestJsonParser
from qa_report_generator.adapters.output.persistence.markdown_writer import MarkdownReportWriter
from qa_report_generator.adapters.output.persistence.markdown_writer.serializers import build_llm_facts_payload
from qa_report_generator.application.use_cases import ReportGenerationService
from qa_report_generator.config import Config
from qa_report_generator.domain.analytics.orchestrator import AnalyticsOrchestrator
from qa_report_generator.domain.models import EnvironmentMeta, Failure, ReportFacts, RunMetrics, TestOutput
from qa_report_generator.domain.value_objects import Duration, TestIdentifier

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_benchmark.fixture import BenchmarkFixture


def _build_failure(index: int) -> Failure:
    return Failure(
        identifier=TestIdentifier(name=f"test_{index}", suite="tests.bench"),
        message="AssertionError: expected True",
        type="AssertionError",
        duration=Duration(seconds=0.01),
        output=TestOutput(stdout="line\n" * 3, stderr=None, log=None),
    )


def _build_metrics(failure_count: int = 10) -> RunMetrics:
    failures = [_build_failure(i) for i in range(failure_count)]
    total = failure_count
    return RunMetrics(
        total=total,
        passed=0,
        failed=failure_count,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=failures,
    )


@pytest.fixture
def fixture_report_path(tmp_path: Path) -> Path:
    """Create a minimal pytest-json-report fixture for parser benchmarks."""
    report_path = tmp_path / "report.json"
    report_path.write_text(
        """
{
  "created": 0,
  "duration": 0.1,
  "exitcode": 1,
  "root": "bench",
  "summary": {"passed": 0, "failed": 1, "skipped": 0, "error": 0, "total": 1},
  "tests": [
    {
      "nodeid": "tests/test_sample.py::test_example",
      "outcome": "failed",
      "call": {"duration": 0.01, "crash": {"message": "boom", "path": "test_sample.py", "lineno": 1}}
    }
  ]
}
""".strip(),
        encoding="utf-8",
    )
    return report_path


def test_benchmark_parser(benchmark: BenchmarkFixture, fixture_report_path: Path) -> None:
    """Benchmark JSON parser performance."""
    parser = PytestJsonParser()

    benchmark(parser.parse, fixture_report_path)


def test_benchmark_analytics_orchestration(benchmark: BenchmarkFixture) -> None:
    """Benchmark analytics orchestration over failures."""
    orchestrator = AnalyticsOrchestrator()
    metrics = _build_metrics()
    environment = EnvironmentMeta(env="bench", build=None, commit=None, target_url=None)

    benchmark(
        orchestrator.build_report_facts,
        metrics=metrics,
        environment=environment,
        input_files=["report.json"],
        failure_clustering_threshold=0.7,
    )


def test_benchmark_llm_payload_serialization(benchmark: BenchmarkFixture) -> None:
    """Benchmark LLM facts payload serialization."""
    metrics = _build_metrics()
    facts = ReportFacts(
        metrics=metrics,
        environment=EnvironmentMeta(env="bench", build=None, commit=None, target_url=None),
        input_files=["report.json"],
    )

    benchmark(
        build_llm_facts_payload,
        facts=facts,
        max_output_lines=20,
        enable_failure_grouping=True,
        max_detailed_failures=10,
    )


def test_benchmark_report_generation_use_case(benchmark: BenchmarkFixture, fixture_report_path: Path) -> None:
    """Benchmark report generation without LLM."""
    parser = PytestJsonParser()
    writer = MarkdownReportWriter(Config())
    service = ReportGenerationService(parser=parser, writer=writer)

    benchmark(
        service.generate,
        report_path=fixture_report_path,
        output_dir=fixture_report_path.parent,
        environment=EnvironmentMeta(env="bench", build=None, commit=None, target_url=None),
        enable_llm=False,
    )
