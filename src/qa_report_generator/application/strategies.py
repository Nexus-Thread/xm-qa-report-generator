"""Prompt strategy selection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.domain.models import RunMetrics


@dataclass(frozen=True)
class PromptStrategy:
    """Prompt strategy and template path."""

    name: str
    template_path: Path


class PromptStrategySelector:
    """Select prompt strategy based on run size."""

    def __init__(
        self,
        detailed_threshold: int = 50,
        summary_threshold: int = 200,
    ) -> None:
        """Initialize prompt selection thresholds."""
        if detailed_threshold < 0 or summary_threshold < 0:
            msg = "Strategy thresholds must be non-negative"
            raise ValueError(msg)
        if detailed_threshold > summary_threshold:
            msg = "Detailed threshold cannot exceed summary threshold"
            raise ValueError(msg)
        self.detailed_threshold = detailed_threshold
        self.summary_threshold = summary_threshold

    def select(self, metrics: RunMetrics) -> PromptStrategy:
        """Select the prompt strategy for a run."""
        total = metrics.total
        if total <= self.detailed_threshold:
            return PromptStrategy(
                name="detailed",
                template_path=self._template_path("prompts_detailed.yaml"),
            )
        if total >= self.summary_threshold:
            return PromptStrategy(
                name="summary",
                template_path=self._template_path("prompts_summary.yaml"),
            )
        return PromptStrategy(
            name="balanced",
            template_path=self._template_path("prompts.yaml"),
        )

    @staticmethod
    def _template_path(filename: str) -> Path:
        return Path(__file__).parents[1] / "templates" / filename
