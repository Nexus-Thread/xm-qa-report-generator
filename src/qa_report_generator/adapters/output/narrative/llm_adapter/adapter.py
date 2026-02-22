"""Large Language Model adapter for generating narrative report sections."""

import logging

import tiktoken
from openai import APIConnectionError, APIError, APITimeoutError, AuthenticationError

from qa_report_generator.adapters.output.narrative.llm_adapter.config import LLMAdapterConfig
from qa_report_generator.adapters.output.narrative.llm_adapter.validators import validate_prompt
from qa_report_generator.adapters.output.narrative.openai import (
    OpenAIClientProtocol,
    OpenAIResponseError,
    build_client,
    extract_message_content,
)
from qa_report_generator.application.ports.output import NarrativeGenerator
from qa_report_generator.domain.exceptions import GenerationError, LLMConnectionError, LLMInitializationError, LLMTimeoutError
from qa_report_generator.domain.value_objects import SectionType

LOGGER = logging.getLogger(__name__)

TOKEN_WARNING_THRESHOLD = 8000


class LLMAdapter(NarrativeGenerator):
    """Adapter for LLM-based narrative generation via OpenAI-compatible APIs."""

    def __init__(self, config: LLMAdapterConfig, client: OpenAIClientProtocol | None = None) -> None:
        """Initialize the LLM adapter with technical configuration."""
        self.model = config.llm_model
        self.base_url = config.llm_base_url
        self.timeout = config.llm_timeout
        self.temperature = config.llm_temperature
        self.reasoning_effort = config.llm_reasoning_effort

        try:
            self.client = client or build_client(config)
            LOGGER.info(
                "LLM initialized: base_url=%s, model=%s, timeout=%.1fs, temperature=%s, reasoning_effort=%s",
                self.base_url,
                self.model,
                self.timeout,
                self.temperature,
                self.reasoning_effort,
            )
        except AuthenticationError as err:
            msg = "Authentication failed for LLM service"
            LOGGER.exception("LLM initialization failed: %s", msg)
            raise LLMInitializationError(
                msg,
                suggestion="Check your LLM_API_KEY environment variable. For local services, use 'not-needed' as the API key.",
            ) from err
        except Exception as err:
            msg = f"Failed to initialize LLM client: {type(err).__name__}: {err}"
            LOGGER.exception("LLM initialization failed: %s", msg)
            raise LLMInitializationError(
                msg,
                suggestion="Verify the configuration is correct and the service is running. Check LOG_LEVEL=DEBUG for more details.",
            ) from err

        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as err:
            msg = f"Failed to initialize token encoder: {type(err).__name__}: {err}"
            LOGGER.exception("Token encoder initialization failed: %s", msg)
            raise LLMInitializationError(
                msg,
                suggestion="Ensure the tiktoken dependency is installed and available.",
            ) from err

    def generate(self, section_type: SectionType, system_prompt: str, user_prompt: str) -> str | None:
        """Generate a narrative section using an LLM."""
        try:
            system_prompt_clean = validate_prompt(system_prompt, "system_prompt")
            user_prompt_clean = validate_prompt(user_prompt, "user_prompt")
            self._log_token_usage(section_type, system_prompt_clean, user_prompt_clean)
            response = self.client.create_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_clean},
                    {"role": "user", "content": user_prompt_clean},
                ],
                temperature=self.temperature,
                reasoning_effort=self.reasoning_effort,
            )
            return extract_message_content(response)
        except OpenAIResponseError as err:
            LOGGER.warning("LLM returned invalid response for section '%s': %s", section_type, err)
            return None
        except (GenerationError, LLMConnectionError, LLMTimeoutError) as err:
            LOGGER.warning("LLM generation failed for section '%s': %s", section_type, err)
            return None
        except (APIConnectionError, APITimeoutError, AuthenticationError, APIError) as err:
            LOGGER.warning("LLM generation failed for section '%s': %s", section_type, err)
            return None

    def _log_token_usage(self, section_type: SectionType, system_prompt: str, user_prompt: str) -> None:
        """Log token usage for prompts when INFO logging is enabled."""
        if not LOGGER.isEnabledFor(logging.INFO):
            return

        system_tokens = len(self.tokenizer.encode(system_prompt))
        user_tokens = len(self.tokenizer.encode(user_prompt))
        total_tokens = system_tokens + user_tokens

        LOGGER.info(
            "Prompt tokens for '%s': system=%d, user=%d, total=%d",
            section_type.value,
            system_tokens,
            user_tokens,
            total_tokens,
        )

        if total_tokens >= TOKEN_WARNING_THRESHOLD:
            LOGGER.warning(
                "High token usage for '%s': %d tokens (threshold=%d)",
                section_type.value,
                total_tokens,
                TOKEN_WARNING_THRESHOLD,
            )
