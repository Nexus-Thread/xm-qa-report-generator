"""Type definitions for LLM adapter."""

from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    """Type-safe structure for chat messages compatible with OpenAI SDK."""

    role: Literal["system", "user", "assistant"]
    content: str
