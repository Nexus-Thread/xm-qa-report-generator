"""Unit tests for markdown writer prompt payload behavior."""

from __future__ import annotations

from qa_report_generator.adapters.output.persistence.markdown_writer.serializers import build_llm_facts_payload
from qa_report_generator.domain.models import EnvironmentMeta, Failure, ReportFacts, RunMetrics, TestOutput
from qa_report_generator.domain.value_objects import Duration, TestIdentifier


def _make_failure(name: str, message: str) -> Failure:
    return Failure(
        identifier=TestIdentifier(name=name, suite="tests.unit"),
        message=message,
        type="AssertionError",
        duration=Duration(seconds=1.0),
        output=None,
    )


def _make_failure_with_output(name: str, message: str, output_lines: int) -> Failure:
    output = TestOutput(stdout="\n".join(f"line{i}" for i in range(output_lines)), stderr=None, log=None)
    return Failure(
        identifier=TestIdentifier(name=name, suite="tests.unit"),
        message=message,
        type="AssertionError",
        duration=Duration(seconds=1.0),
        output=output,
    )


def _make_facts(failures: list[Failure]) -> ReportFacts:
    metrics = RunMetrics(
        total=len(failures),
        passed=0,
        failed=len(failures),
        skipped=0,
        errors=0,
        duration=Duration(seconds=2.0),
        failures=failures,
    )
    return ReportFacts(
        metrics=metrics,
        environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
        input_files=["report.json"],
    )


def test_llm_payload_respects_grouping_toggle() -> None:
    """Failure grouping can be disabled to emit individual failures."""
    failures = [_make_failure("test_one", "boom"), _make_failure("test_two", "boom")]
    facts = _make_facts(failures)

    payload = build_llm_facts_payload(
        facts,
        max_output_lines=20,
        enable_failure_grouping=False,
        max_detailed_failures=10,
    )

    grouped = payload["metrics"]["failures"]
    assert len(grouped) == len(failures)
    assert all(item["count"] == 1 for item in grouped)


def test_llm_payload_limits_detailed_failures() -> None:
    """Detailed failures payload respects config cap."""
    failures = [_make_failure(f"test_{i}", f"boom-{i}") for i in range(5)]
    facts = _make_facts(failures)

    payload = build_llm_facts_payload(
        facts,
        max_output_lines=20,
        enable_failure_grouping=True,
        max_detailed_failures=2,
    )

    detailed = payload["metrics"]["detailed_failures"]
    assert len(detailed) == 2
    assert detailed[0]["test_name"] == "test_0"
    assert detailed[1]["test_name"] == "test_1"


def test_llm_payload_truncates_output_lines() -> None:
    """Detailed failure payload truncates output lines based on config."""
    failure = _make_failure_with_output("test_one", "boom", output_lines=5)
    facts = _make_facts([failure])

    payload = build_llm_facts_payload(
        facts,
        max_output_lines=2,
        enable_failure_grouping=True,
        max_detailed_failures=10,
    )

    detailed = payload["metrics"]["detailed_failures"][0]
    stdout = detailed["output"]["stdout"]
    assert "line0" in stdout
    assert "line1" in stdout
    assert "truncated" in stdout
