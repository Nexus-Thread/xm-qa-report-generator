"""Narrative generation adapter using an OpenAI-compatible LLM transport."""

import logging

from openai import APIConnectionError, APIError, APITimeoutError, AuthenticationError

from qa_report_generator.adapters.output.narrative.narrative_adapter.config import NarrativeAdapterConfig
from qa_report_generator.adapters.output.narrative.narrative_adapter.validators import validate_prompt
from qa_report_generator.adapters.output.narrative.openai import OpenAIClientProtocol, OpenAIResponseError, extract_message_content
from qa_report_generator.application.dtos import SectionPrompt
from qa_report_generator.application.ports.output import NarrativeGenerator
from qa_report_generator.domain.exceptions import GenerationError, LLMConnectionError, LLMTimeoutError

LOGGER = logging.getLogger(__name__)


class NarrativeAdapter(NarrativeGenerator):
    """Generates narrative sections using an OpenAI-compatible LLM transport."""

    def __init__(self, config: NarrativeAdapterConfig, client: OpenAIClientProtocol) -> None:
        """Initialize with a config and transport client."""
        self.model = config.llm_model
        self.client = client

        LOGGER.info("NarrativeAdapter initialized: model=%s", self.model)

    def generate(self, section_prompt: SectionPrompt, user_prompt: str) -> str | None:
        """Generate a narrative section using the configured LLM transport."""
        section_label = section_prompt.section_type.value
        try:
            system_prompt_clean = validate_prompt(section_prompt.system_prompt, "system_prompt")
            user_prompt_clean = validate_prompt(user_prompt, "user_prompt")
            response = self.client.create_chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt_clean},
                    {"role": "user", "content": user_prompt_clean},
                ],
            )
            return extract_message_content(response)
        except OpenAIResponseError as err:
            LOGGER.warning("LLM returned invalid response for section '%s': %s", section_label, err)
            return None
        except (GenerationError, LLMConnectionError, LLMTimeoutError) as err:
            LOGGER.warning("LLM generation failed for section '%s': %s", section_label, err)
            return None
        except (APIConnectionError, APITimeoutError, AuthenticationError, APIError) as err:
            LOGGER.warning("LLM generation failed for section '%s': %s", section_label, err)
            return None
