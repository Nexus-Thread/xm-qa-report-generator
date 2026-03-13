"""Shared LLM adapter exports."""

from .openai_adapter import (
    OpenAIClient,
    OpenAIClientProtocol,
    OpenAIClientSettings,
    OpenAIResponseError,
    OpenAIResponseUsage,
    build_client,
    extract_message_content,
    extract_usage,
)
from .structured_llm_adapter import (
    OpenAIStructuredLlmAdapter,
    StructuredLlmError,
    StructuredLlmInvalidJsonError,
    StructuredLlmJsonCompletionResult,
    StructuredLlmResponseError,
)

__all__ = [
    "OpenAIClient",
    "OpenAIClientProtocol",
    "OpenAIClientSettings",
    "OpenAIResponseError",
    "OpenAIResponseUsage",
    "OpenAIStructuredLlmAdapter",
    "StructuredLlmError",
    "StructuredLlmInvalidJsonError",
    "StructuredLlmJsonCompletionResult",
    "StructuredLlmResponseError",
    "build_client",
    "extract_message_content",
    "extract_usage",
]
