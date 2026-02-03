"""Unit tests for application use cases."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from qa_report_generator.application.use_cases import ReportGenerationService
from qa_report_generator.domain.exceptions import ReportingError
from qa_report_generator.domain.models import EnvironmentMeta, RunMetrics
from qa_report_generator.domain.value_objects import Duration


def _make_metrics() -> RunMetrics:
    return RunMetrics(
        total=1,
        passed=1,
        failed=0,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=[],
    )


def test_report_generation_logs_timings(caplog: Any) -> None:
    """Ensure timing summary log is emitted on report generation."""
    parser = Mock()
    parser.parse.return_value = _make_metrics()
    writer = Mock()
    writer.save_reports.return_value = (Path("summary.md"), Path("signoff.md"))
    narrative = Mock()

    service = ReportGenerationService(parser, writer, narrative)

    with caplog.at_level("INFO"):
        service.generate(
            report_path=Path("report.json"),
            output_dir=Path("out"),
            environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
            enable_llm=True,
        )

    assert any("Report generated in" in record.message and record.levelname == "INFO" for record in caplog.records)


def test_report_generation_uses_failure_clustering_threshold() -> None:
    """Use the configured failure clustering threshold."""
    parser = Mock()
    parser.parse.return_value = _make_metrics()
    writer = Mock()
    writer.save_reports.return_value = (Path("summary.md"), Path("signoff.md"))
    narrative = Mock()

    service = ReportGenerationService(
        parser,
        writer,
        narrative,
        failure_clustering_threshold=0.9,
    )

    orchestrator = Mock()
    orchestrator.build_report_facts.side_effect = ValueError("boom")
    service._analytics_orchestrator = orchestrator  # noqa: SLF001

    with pytest.raises(ReportingError, match="ValueError: boom"):
        service.generate(
            report_path=Path("report.json"),
            output_dir=Path("out"),
            environment=EnvironmentMeta(env="test", build="1", commit=None, target_url=None),
            enable_llm=True,
        )

    orchestrator.build_report_facts.assert_called_once()
    _, kwargs = orchestrator.build_report_facts.call_args
    assert kwargs["failure_clustering_threshold"] == 0.9
