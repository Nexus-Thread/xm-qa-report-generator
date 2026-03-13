"""Application-specific tracker for aggregated OpenAI usage and estimated cost."""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from qa_report_generator_performance.application.dtos import LlmUsageSummary

if TYPE_CHECKING:
    from shared.adapters.output.llm import OpenAIResponseUsage

TOKENS_PER_MILLION = 1_000_000


class OpenAILlmUsageTracker:
    """Track aggregated token usage across multiple OpenAI-backed LLM calls."""

    def __init__(
        self,
        *,
        input_cost_per_million_tokens: float | None = None,
        output_cost_per_million_tokens: float | None = None,
    ) -> None:
        """Store optional pricing and initialize empty usage state."""
        if input_cost_per_million_tokens is not None and input_cost_per_million_tokens < 0:
            msg = "input_cost_per_million_tokens must be greater than or equal to 0"
            raise ValueError(msg)
        if output_cost_per_million_tokens is not None and output_cost_per_million_tokens < 0:
            msg = "output_cost_per_million_tokens must be greater than or equal to 0"
            raise ValueError(msg)

        self._input_cost_per_million_tokens = input_cost_per_million_tokens
        self._output_cost_per_million_tokens = output_cost_per_million_tokens
        self._lock = Lock()
        self._reset_unlocked()

    def reset(self) -> None:
        """Clear all previously recorded usage state."""
        with self._lock:
            self._reset_unlocked()

    def record_usage(self, *, usage: OpenAIResponseUsage | None) -> None:
        """Record one LLM response usage snapshot."""
        with self._lock:
            self._request_count += 1

            if usage is None:
                self._prompt_tokens_complete = False
                self._completion_tokens_complete = False
                self._total_tokens_complete = False
                return

            if usage.prompt_tokens is None:
                self._prompt_tokens_complete = False
            else:
                self._prompt_tokens += usage.prompt_tokens

            if usage.completion_tokens is None:
                self._completion_tokens_complete = False
            else:
                self._completion_tokens += usage.completion_tokens

            if usage.total_tokens is None:
                self._total_tokens_complete = False
            else:
                self._total_tokens += usage.total_tokens

    def build_summary(self) -> LlmUsageSummary | None:
        """Return an immutable snapshot of aggregated usage for the current run."""
        with self._lock:
            if self._request_count == 0:
                return None

            prompt_tokens = self._prompt_tokens if self._prompt_tokens_complete else None
            completion_tokens = self._completion_tokens if self._completion_tokens_complete else None
            total_tokens = self._build_total_tokens(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
            estimated_cost_usd = self._build_estimated_cost(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

            return LlmUsageSummary(
                request_count=self._request_count,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                estimated_cost_usd=estimated_cost_usd,
            )

    def _build_total_tokens(self, *, prompt_tokens: int | None, completion_tokens: int | None) -> int | None:
        """Return total tokens from direct totals or complete prompt/completion sums."""
        if self._total_tokens_complete:
            return self._total_tokens
        if prompt_tokens is None or completion_tokens is None:
            return None
        return prompt_tokens + completion_tokens

    def _build_estimated_cost(self, *, prompt_tokens: int | None, completion_tokens: int | None) -> float | None:
        """Return estimated USD cost when token counts and pricing are both available."""
        if prompt_tokens is None or completion_tokens is None:
            return None
        if self._input_cost_per_million_tokens is None or self._output_cost_per_million_tokens is None:
            return None

        input_cost = prompt_tokens * self._input_cost_per_million_tokens / TOKENS_PER_MILLION
        output_cost = completion_tokens * self._output_cost_per_million_tokens / TOKENS_PER_MILLION
        return input_cost + output_cost

    def _reset_unlocked(self) -> None:
        """Initialize mutable counters while the caller already holds the lock."""
        self._request_count = 0
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._total_tokens = 0
        self._prompt_tokens_complete = True
        self._completion_tokens_complete = True
        self._total_tokens_complete = True
