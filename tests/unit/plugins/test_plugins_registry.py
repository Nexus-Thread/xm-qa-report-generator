"""Unit tests for plugin registries and discovery helpers."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from qa_report_generator.application.dtos import ParsedReport
from qa_report_generator.application.ports.output import NarrativeGenerator, ReportParser, ReportWriter
from qa_report_generator.domain.models import ReportFacts, RunMetrics
from qa_report_generator.domain.value_objects import Duration
from qa_report_generator.plugins.registry import (
    HookRegistry,
    ParserRegistry,
    WriterRegistry,
    discover_plugins,
)

if TYPE_CHECKING:
    from pathlib import Path


class DummyParser(ReportParser):
    """Minimal parser implementation for registry testing."""

    def parse(self, filepath: Path) -> ParsedReport:  # pragma: no cover - interface stub
        """Return an empty ParsedReport object for registry validation."""
        _ = filepath
        return ParsedReport(
            metrics=RunMetrics(
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                errors=0,
                duration=Duration(seconds=0.0),
                failures=[],
            )
        )


class DummyWriter(ReportWriter):
    """Minimal writer implementation for registry testing."""

    def save_reports(
        self,
        facts: ReportFacts,
        output_dir: Path,
        narrative_generator: NarrativeGenerator | None = None,
        prompt_template_path: Path | None = None,
    ) -> tuple[Path, Path]:  # pragma: no cover - interface stub
        """Return placeholder report paths for registry validation."""
        _ = facts
        _ = narrative_generator
        _ = prompt_template_path
        return output_dir / "summary.md", output_dir / "signoff.md"


@pytest.fixture(autouse=True)
def clear_registries() -> None:
    """Reset registries between tests."""
    ParserRegistry.clear()
    WriterRegistry.clear()
    HookRegistry.clear()


def test_parser_registry_lists_plugins() -> None:
    """Ensure parser registry exposes registered plugins."""
    ParserRegistry.register("dummy", DummyParser)

    assert ParserRegistry.get("dummy") is DummyParser
    assert ParserRegistry.list_available() == ["dummy"]
    assert ParserRegistry.list_plugins() == {"dummy": DummyParser}


def test_writer_registry_lists_plugins() -> None:
    """Ensure writer registry exposes registered plugins."""
    WriterRegistry.register("dummy", DummyWriter)

    assert WriterRegistry.get("dummy") is DummyWriter
    assert WriterRegistry.list_available() == ["dummy"]
    assert WriterRegistry.list_plugins() == {"dummy": DummyWriter}


def test_hook_registry_lists_hooks() -> None:
    """Ensure hook registry exposes registered hooks."""

    def hook(context: dict[str, object]) -> None:
        _ = context

    HookRegistry.register("post_write", hook)

    assert HookRegistry.get_hooks("post_write") == [hook]
    assert HookRegistry.list_hooks()["post_write"] == [hook]


def test_hook_registry_invalid_hook_point() -> None:
    """Ensure invalid hook points raise a ValueError."""
    with pytest.raises(ValueError, match="Invalid hook point"):
        HookRegistry.register("unknown", Mock())


def test_discover_plugins_imports_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure module-based plugin discovery triggers imports."""
    imported = []

    def fake_import(name: str) -> None:
        imported.append(name)

    monkeypatch.setattr("qa_report_generator.plugins.registry.import_module", fake_import)

    def fake_entry_points() -> SimpleNamespace:
        def select(*, group: str) -> list[object]:
            _ = group
            return []

        return SimpleNamespace(select=select)

    monkeypatch.setattr("qa_report_generator.plugins.registry.entry_points", fake_entry_points)

    discover_plugins(["examples.custom_writer.json_writer", "examples.hooks.teams_notifier"])

    assert imported == ["examples.custom_writer.json_writer", "examples.hooks.teams_notifier"]
