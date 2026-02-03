"""Large Language Model adapter for generating narrative report sections."""

import logging

import tiktoken
from openai import AuthenticationError, OpenAI

from qa_report_generator.adapters.output.narrative.llm_adapter.config import LLMAdapterConfig
from qa_report_generator.adapters.output.narrative.llm_adapter.retry_handler import RetryHandler
from qa_report_generator.adapters.output.narrative.llm_adapter.validators import validate_prompt
from qa_report_generator.application.ports.output import NarrativeGenerator
from qa_report_generator.domain.exceptions import (
    GenerationError,
    LLMConnectionError,
    LLMInitializationError,
    LLMTimeoutError,
)
from qa_report_generator.domain.value_objects import SectionType

logger = logging.getLogger(__name__)

TOKEN_WARNING_THRESHOLD = 8000


class LLMAdapter(NarrativeGenerator):
    """Adapter for LLM-based narrative generation via OpenAI-compatible APIs."""

    def __init__(self, config: LLMAdapterConfig, client: OpenAI | None = None) -> None:
        """Initialize the LLM adapter with technical configuration.

        This is a pure technical adapter; prompts are passed as parameters.

        Args:
            config: Technical configuration for the adapter (timeout, retries, etc.)
            client: Optional OpenAI client override (primarily for tests)

        Raises:
            LLMInitializationError: If the client cannot be initialized.

        """
        self.model = config.llm_model
        self.base_url = config.llm_base_url
        self.timeout = config.llm_timeout
        self.temperature = config.llm_temperature
        self.reasoning_effort = config.llm_reasoning_effort

        try:
            self.client = client or OpenAI(
                base_url=self.base_url,
                api_key=config.llm_api_key,
                timeout=self.timeout,
            )

            logger.info(
                "LLM initialized: base_url=%s, model=%s, timeout=%.1fs, temperature=%s, reasoning_effort=%s",
                self.base_url,
                self.model,
                self.timeout,
                self.temperature,
                self.reasoning_effort,
            )

        except AuthenticationError as e:
            msg = "Authentication failed for LLM service"
            logger.exception("LLM initialization failed: %s", msg)
            raise LLMInitializationError(
                msg,
                suggestion="Check your LLM_API_KEY environment variable. For local services, use 'not-needed' as the API key.",
            ) from e
        except Exception as e:
            msg = f"Failed to initialize LLM client: {type(e).__name__}: {e}"
            logger.exception("LLM initialization failed: %s", msg)
            raise LLMInitializationError(
                msg,
                suggestion="Verify the configuration is correct and the service is running. Check LOG_LEVEL=DEBUG for more details.",
            ) from e

        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            msg = f"Failed to initialize token encoder: {type(e).__name__}: {e}"
            logger.exception("Token encoder initialization failed: %s", msg)
            raise LLMInitializationError(
                msg,
                suggestion="Ensure the tiktoken dependency is installed and available.",
            ) from e

        self.retry_handler = RetryHandler(
            client=self.client,
            model=self.model,
            base_url=self.base_url,
            max_retries=config.llm_max_retries,
            retry_backoff_factor=config.llm_retry_backoff_factor,
        )

    def generate(
        self,
        section_type: SectionType,
        system_prompt: str,
        user_prompt: str,
    ) -> str | None:
        """Generate a narrative section using an LLM.

        Pure technical method; receives prompts from the business layer.

        Args:
            section_type: Type of section to generate (for logging)
            system_prompt: System-level instructions from the business layer
            user_prompt: User-level prompt with section-specific requirements

        Returns:
            Generated text or None if the LLM is unavailable

        """
        try:
            system_prompt_clean = validate_prompt(system_prompt, "system_prompt")
            user_prompt_clean = validate_prompt(user_prompt, "user_prompt")
            self._log_token_usage(section_type, system_prompt_clean, user_prompt_clean)
            return self.retry_handler.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt_clean},
                    {"role": "user", "content": user_prompt_clean},
                ],
                temperature=self.temperature,
                reasoning_effort=self.reasoning_effort,
            )
        except (GenerationError, LLMConnectionError, LLMTimeoutError) as e:
            logger.warning("LLM generation failed for section '%s': %s", section_type, e)
            return None

    def _log_token_usage(self, section_type: SectionType, system_prompt: str, user_prompt: str) -> None:
        """Log token usage for prompts (only when INFO logging is enabled).

        Tokenization is expensive; this method short-circuits when logging is disabled
        to avoid unnecessary work on the critical path.
        """
        if not logger.isEnabledFor(logging.INFO):
            return

        system_tokens = len(self.tokenizer.encode(system_prompt))
        user_tokens = len(self.tokenizer.encode(user_prompt))
        total_tokens = system_tokens + user_tokens

        logger.info(
            "Prompt tokens for '%s': system=%d, user=%d, total=%d",
            section_type.value,
            system_tokens,
            user_tokens,
            total_tokens,
        )

        if total_tokens >= TOKEN_WARNING_THRESHOLD:
            logger.warning(
                "High token usage for '%s': %d tokens (threshold=%d)",
                section_type.value,
                total_tokens,
                TOKEN_WARNING_THRESHOLD,
            )
