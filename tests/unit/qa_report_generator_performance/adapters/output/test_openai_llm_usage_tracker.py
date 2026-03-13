"""Unit tests for aggregated OpenAI usage tracking."""

from __future__ import annotations

import pytest

from qa_report_generator_performance.adapters.output.structured_llm_adapter import OpenAILlmUsageTracker
from qa_report_generator_performance.application.dtos import LlmUsageSummary
from shared.adapters.output.llm import OpenAIResponseUsage


def test_usage_tracker_aggregates_tokens_and_estimated_cost() -> None:
    """Usage tracker aggregates multiple calls into one immutable summary."""
    tracker = OpenAILlmUsageTracker(
        input_cost_per_million_tokens=2.5,
        output_cost_per_million_tokens=10.0,
    )

    tracker.record_usage(usage=OpenAIResponseUsage(prompt_tokens=1000, completion_tokens=200, total_tokens=1200))
    tracker.record_usage(usage=OpenAIResponseUsage(prompt_tokens=500, completion_tokens=100, total_tokens=600))

    assert tracker.build_summary() == LlmUsageSummary(
        request_count=2,
        prompt_tokens=1500,
        completion_tokens=300,
        total_tokens=1800,
        estimated_cost_usd=0.00675,
    )


def test_usage_tracker_returns_unavailable_fields_when_usage_missing() -> None:
    """Usage tracker preserves request count even when usage metadata is absent."""
    tracker = OpenAILlmUsageTracker()

    tracker.record_usage(usage=None)

    assert tracker.build_summary() == LlmUsageSummary(
        request_count=1,
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=None,
        estimated_cost_usd=None,
    )


def test_usage_tracker_reset_clears_previous_summary() -> None:
    """Usage tracker reset clears all accumulated usage state."""
    tracker = OpenAILlmUsageTracker()
    tracker.record_usage(usage=OpenAIResponseUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15))

    tracker.reset()

    assert tracker.build_summary() is None


@pytest.mark.parametrize(
    ("input_cost_per_million_tokens", "output_cost_per_million_tokens"),
    [(-1.0, None), (None, -1.0)],
)
def test_usage_tracker_rejects_negative_pricing(
    input_cost_per_million_tokens: float | None,
    output_cost_per_million_tokens: float | None,
) -> None:
    """Usage tracker rejects negative pricing values."""
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        OpenAILlmUsageTracker(
            input_cost_per_million_tokens=input_cost_per_million_tokens,
            output_cost_per_million_tokens=output_cost_per_million_tokens,
        )
