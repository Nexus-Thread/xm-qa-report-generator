"""Input validation utilities for LLM adapter."""

from qa_report_generator.adapters.output.narrative.llm_adapter.types import ChatMessage
from qa_report_generator.domain.exceptions import GenerationError


def validate_prompt(prompt: str, prompt_name: str) -> str:
    """Validate and normalize a prompt string.

    Args:
        prompt: The prompt to validate
        prompt_name: Name for error messages

    Returns:
        Stripped prompt string

    Raises:
        GenerationError: If prompt is empty or whitespace-only

    """
    if not prompt or not prompt.strip():
        msg = f"{prompt_name} cannot be empty"
        raise GenerationError(
            msg,
            suggestion="Ensure prompts are populated with template content before calling the adapter.",
        )
    return prompt.strip()


def validate_messages(messages: list[ChatMessage]) -> None:
    """Validate chat messages for LLM request.

    Args:
        messages: List of messages to validate

    Raises:
        GenerationError: If messages are empty or have empty content

    """
    if not messages:
        msg = "LLM messages cannot be empty"
        raise GenerationError(
            msg,
            suggestion="Provide system and user messages when calling the adapter.",
        )

    for message in messages:
        content = message.get("content", "")
        if not content or not content.strip():
            msg = f"LLM message content cannot be empty (role={message.get('role')})"
            raise GenerationError(
                msg,
                suggestion="Ensure each message has non-empty content before sending.",
            )
