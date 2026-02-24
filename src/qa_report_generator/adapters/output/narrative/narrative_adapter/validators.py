"""Input validation utilities for the narrative adapter."""

from qa_report_generator.domain.exceptions import GenerationError


def validate_prompt(prompt: str, prompt_name: str) -> str:
    """Validate and normalize a prompt string.

    Args:
        prompt: Prompt to validate
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
