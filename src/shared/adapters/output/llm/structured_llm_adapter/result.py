"""Structured LLM completion result DTOs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shared.adapters.output.llm.openai_adapter import OpenAIResponseUsage


@dataclass(frozen=True, slots=True)
class StructuredLlmJsonCompletionResult:
    """Structured JSON completion payload plus optional OpenAI usage metadata."""

    payload: dict[str, Any]
    usage: OpenAIResponseUsage | None
