"""DTOs describing aggregated LLM usage for one CLI run."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LlmUsageSummary:
    """Aggregated token usage and estimated cost for one extraction run."""

    request_count: int
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: float | None
