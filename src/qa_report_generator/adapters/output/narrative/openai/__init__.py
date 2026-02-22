"""OpenAI transport client utilities."""

from qa_report_generator.adapters.output.narrative.openai.constants import (
    DEFAULT_BACKOFF_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_VERIFY_SSL,
)
from qa_report_generator.adapters.output.narrative.openai.factory import (
    OpenAIClientSettings,
    OpenAIClientSettingsProtocol,
    build_client,
)
from qa_report_generator.adapters.output.narrative.openai.protocols import OpenAIClientProtocol
from qa_report_generator.adapters.output.narrative.openai.response import (
    OpenAIResponseError,
    OpenAIResponseUsage,
    extract_message_content,
    extract_usage,
)
from qa_report_generator.adapters.output.narrative.openai.transport import OpenAIClient

__all__ = [
    "DEFAULT_BACKOFF_SECONDS",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_VERIFY_SSL",
    "OpenAIClient",
    "OpenAIClientProtocol",
    "OpenAIClientSettings",
    "OpenAIClientSettingsProtocol",
    "OpenAIResponseError",
    "OpenAIResponseUsage",
    "build_client",
    "extract_message_content",
    "extract_usage",
]
