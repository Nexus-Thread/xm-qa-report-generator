"""Narrative generation adapter using an OpenAI-compatible LLM transport."""

import logging

import tiktoken
from openai import APIConnectionError, APIError, APITimeoutError, AuthenticationError

from qa_report_generator.adapters.output.narrative.narrative_adapter.config import NarrativeAdapterConfig
from qa_report_generator.adapters.output.narrative.narrative_adapter.validators import validate_prompt
from qa_report_generator.adapters.output.narrative.openai import OpenAIClientProtocol, OpenAIResponseError, extract_message_content
from qa_report_generator.application.ports.output import NarrativeGenerator
from qa_report_generator.domain.exceptions import GenerationError, LLMConnectionError, LLMInitializationError, LLMTimeoutError
from qa_report_generator.domain.value_objects import SectionType

LOGGER = logging.getLogger(__name__)

TOKEN_WARNING_THRESHOLD = 8000


class NarrativeAdapter(NarrativeGenerator):
    """Adapter that fulfils the NarrativeGenerator port via an OpenAI-compatible transport."""

    def __init__(self, config: NarrativeAdapterConfig, client: OpenAIClientProtocol) -> None:
        """Initialize the narrative adapter with a pre-built transport client."""
        self.model = config.llm_model
        self.client = client

        LOGGER.info("NarrativeAdapter initialized: model=%s", self.model)

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
        """Generate a narrative section using the configured LLM transport."""
        try:
            system_prompt_clean = validate_prompt(system_prompt, "system_prompt")
            user_prompt_clean = validate_prompt(user_prompt, "user_prompt")
            self._log_token_usage(section_type, system_prompt_clean, user_prompt_clean)
            response = self.client.create_chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_clean},
                    {"role": "user", "content": user_prompt_clean},
                ],
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
