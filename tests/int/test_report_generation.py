"""Integration tests for report generation workflow."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import Mock

from qa_report_generator.adapters.output.parsers import PytestJsonParser
from qa_report_generator.adapters.output.persistence.markdown_writer import MarkdownReportWriter
from qa_report_generator.application.use_cases import ReportGenerationService
from qa_report_generator.config import Config
from qa_report_generator.domain.models import EnvironmentMeta
from qa_report_generator.templates import PromptTemplate

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from qa_report_generator.application.ports.output import NarrativeGenerator


def _write_pytest_report(path: Path) -> None:
    payload = {
        "summary": {
            "total": 2,
            "passed": 1,
            "failed": 1,
            "skipped": 0,
            "error": 0,
        },
        "duration": 1.2,
        "tests": [
            {
                "nodeid": "tests/test_alpha.py::test_pass",
                "outcome": "passed",
                "duration": 0.2,
            },
            {
                "nodeid": "tests/test_beta.py::test_fail",
                "outcome": "failed",
                "duration": 0.3,
                "call": {
                    "longrepr": {
                        "reprcrash": {
                            "message": "AssertionError: boom",
                            "path": "AssertionError",
                        },
                    },
                },
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _make_prompt_template() -> PromptTemplate:
    return PromptTemplate(
        system_prompt="sys",
        section_prompts={
            "executive_summary": "exec {facts_json}",
            "key_observations": "obs {facts_json}",
            "risk_assessment": "risk {facts_json}",
            "recommendation": "reco {facts_json}",
        },
    )


def _make_narrative_generator() -> NarrativeGenerator:
    generator = Mock()
    generator.generate.return_value = "Generated content"
    return generator


def test_report_generation_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Parse → generate → write workflow should emit report files."""
    report_path = tmp_path / "report.json"
    _write_pytest_report(report_path)
    output_dir = tmp_path / "out"
    config = Config()
    parser = PytestJsonParser()
    writer = MarkdownReportWriter(config)
    narrative = _make_narrative_generator()

    monkeypatch.setattr(
        "qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_default",
        Mock(return_value=_make_prompt_template()),
    )

    service = ReportGenerationService(parser, writer, narrative)
    result = service.generate(
        report_path=report_path,
        output_dir=output_dir,
        environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
        enable_llm=True,
    )

    assert result.summary_path.exists()
    assert result.signoff_path.exists()
    assert "Pytest Run Summary" in result.summary_path.read_text(encoding="utf-8")
    assert "QA Sign-Off Report" in result.signoff_path.read_text(encoding="utf-8")


def test_report_generation_without_llm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generation should succeed without LLM narrative content."""
    report_path = tmp_path / "report.json"
    _write_pytest_report(report_path)
    output_dir = tmp_path / "out"
    config = Config()
    parser = PytestJsonParser()

    monkeypatch.setattr(
        "qa_report_generator.adapters.output.persistence.markdown_writer.adapter.PromptLoader.load_default",
        Mock(return_value=_make_prompt_template()),
    )

    writer = MarkdownReportWriter(config)

    service = ReportGenerationService(parser, writer, narrative_generator=None)
    result = service.generate(
        report_path=report_path,
        output_dir=output_dir,
        environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
        enable_llm=False,
    )

    assert result.summary_path.exists()
    assert result.signoff_path.exists()
    assert "LLM unavailable" in result.summary_path.read_text(encoding="utf-8")
