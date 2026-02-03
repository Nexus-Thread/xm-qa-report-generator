"""Unit tests for prompt strategy selection."""

from __future__ import annotations

from qa_report_generator.application.strategies import PromptStrategySelector
from qa_report_generator.domain.models import RunMetrics
from qa_report_generator.domain.value_objects import Duration


def _make_metrics(total: int) -> RunMetrics:
    return RunMetrics(
        total=total,
        passed=total,
        failed=0,
        skipped=0,
        errors=0,
        duration=Duration(seconds=1.0),
        failures=[],
    )


def test_selects_detailed_strategy_for_small_runs() -> None:
    """Selects detailed prompts for small test runs."""
    selector = PromptStrategySelector()
    strategy = selector.select(_make_metrics(10))

    assert strategy.name == "detailed"
    assert strategy.template_path.name == "prompts_detailed.yaml"


def test_selects_summary_strategy_for_large_runs() -> None:
    """Selects summary prompts for large test runs."""
    selector = PromptStrategySelector()
    strategy = selector.select(_make_metrics(250))

    assert strategy.name == "summary"
    assert strategy.template_path.name == "prompts_summary.yaml"


def test_selects_balanced_strategy_for_medium_runs() -> None:
    """Selects balanced prompts for mid-sized test runs."""
    selector = PromptStrategySelector()
    strategy = selector.select(_make_metrics(120))

    assert strategy.name == "balanced"
    assert strategy.template_path.name == "prompts.yaml"
