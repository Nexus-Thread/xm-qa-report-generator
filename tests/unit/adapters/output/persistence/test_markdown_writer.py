"""Unit tests for markdown report writer rendering."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from qa_report_generator.adapters.output.persistence.markdown_writer import MarkdownReportWriter
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.domain.models import EnvironmentMeta, Failure, ReportFacts, RunMetrics, TestOutput
from qa_report_generator.domain.value_objects import Duration, SectionType, TestIdentifier
from qa_report_generator.templates import PromptTemplate

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _make_failure(name: str, message: str, *, with_output: bool = False) -> Failure:
    output = None
    if with_output:
        output = TestOutput(stdout="out", stderr="err", log="log")
    return Failure(
        identifier=TestIdentifier(name=name, suite="tests.unit"),
        message=message,
        type="AssertionError",
        duration=Duration(seconds=1.0),
        output=output,
    )


def _make_facts(failures: list[Failure]) -> ReportFacts:
    passed = 1 if not failures else 0
    total = passed + len(failures)
    metrics = RunMetrics(
        total=total,
        passed=passed,
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


def _make_prompt_template() -> PromptTemplate:
    return PromptTemplate(
        system_prompt="sys",
        section_prompts={
            SectionType.EXECUTIVE_SUMMARY.value: "exec {facts_json}",
            SectionType.KEY_OBSERVATIONS.value: "obs {facts_json}",
            SectionType.RISK_ASSESSMENT.value: "risk {facts_json}",
            SectionType.RECOMMENDATION.value: "reco {facts_json}",
        },
    )


def _make_narrative_generator() -> Mock:
    generator = Mock()
    generator.generate.return_value = "Generated content"
    return generator


def test_save_reports_writes_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Writer should render and save summary and sign-off reports."""
    facts = _make_facts([])
    monkeypatch.setattr(
        "qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_default",
        Mock(return_value=_make_prompt_template()),
    )
    writer = MarkdownReportWriter(AppSettings())

    summary_path, signoff_path = writer.save_reports(facts, tmp_path)

    assert summary_path.exists()
    assert signoff_path.exists()
    assert "Pytest Run Summary" in summary_path.read_text(encoding="utf-8")
    assert "QA Sign-Off Report" in signoff_path.read_text(encoding="utf-8")


def test_render_summary_includes_sections(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Summary report should include key deterministic sections."""
    facts = _make_facts([_make_failure("test_one", "boom")])
    monkeypatch.setattr(
        "qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_default",
        Mock(return_value=_make_prompt_template()),
    )
    writer = MarkdownReportWriter(AppSettings())

    summary_path, _ = writer.save_reports(facts, tmp_path, narrative_generator=None)
    content = summary_path.read_text(encoding="utf-8")

    assert "Run Facts" in content
    assert "Executive Summary" in content
    assert "Key Observations" in content
    assert "Engineering Summary" in content
    assert "Top Failures" in content
    assert "Input Artifacts" in content


def test_render_signoff_includes_critical_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Sign-off report should include critical failures when present."""
    failures = [_make_failure("test_one", "boom")]
    facts = _make_facts(failures)
    monkeypatch.setattr(
        "qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_default",
        Mock(return_value=_make_prompt_template()),
    )
    writer = MarkdownReportWriter(AppSettings())

    _, signoff_path = writer.save_reports(facts, tmp_path, narrative_generator=None)
    content = signoff_path.read_text(encoding="utf-8")

    assert "Test Results Overview" in content
    assert "Pass Rate" in content
    assert "Critical Failures" in content
    assert "Sign-Off" in content


def test_render_failures_truncates_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Failure rendering should include captured output when available."""
    failure = _make_failure("test_one", "boom", with_output=True)
    facts = _make_facts([failure])
    monkeypatch.setattr(
        "qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_default",
        Mock(return_value=_make_prompt_template()),
    )
    writer = MarkdownReportWriter(AppSettings(max_output_lines_per_failure=1))

    summary_path, _ = writer.save_reports(facts, tmp_path, narrative_generator=None)
    content = summary_path.read_text(encoding="utf-8")

    assert "Captured stdout" in content
    assert "Captured stderr" in content
    assert "Captured log" in content


def test_generate_sections_parallel_uses_narrative_generator(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Narrative generation should invoke generator for each section type."""
    facts = _make_facts([])
    generator = _make_narrative_generator()
    monkeypatch.setattr(
        "qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_default",
        Mock(return_value=_make_prompt_template()),
    )
    writer = MarkdownReportWriter(AppSettings())

    writer.save_reports(facts, tmp_path, narrative_generator=generator)

    generator.generate.assert_called()


def test_save_reports_reload_prompt_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Passing a different prompt template path should reload templates."""
    facts = _make_facts([])
    loader_mock = Mock(return_value=_make_prompt_template())
    monkeypatch.setattr("qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_default", loader_mock)
    monkeypatch.setattr("qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_from_file", loader_mock)
    writer = MarkdownReportWriter(AppSettings())
    prompt_path = tmp_path / "custom.yaml"
    prompt_path.write_text("x: y", encoding="utf-8")

    writer.save_reports(facts, tmp_path, prompt_template_path=prompt_path)

    loader_mock.assert_called()
