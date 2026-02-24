"""Prompt template loading and management.

This module provides classes for loading prompt templates from YAML files
and managing their interpolation with runtime variables.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

from qa_report_generator.domain.exceptions import ConfigurationError
from qa_report_generator.domain.value_objects import SectionType

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Container for prompt templates with variable interpolation.

    Stores system and section-specific prompts and provides methods to retrieve
    them with runtime variable interpolation.
    """

    def __init__(self, system_prompt: str, section_prompts: dict[str, str]) -> None:
        """Initialize prompt template.

        Args:
            system_prompt: System-level prompt that sets LLM behavior
            section_prompts: Dictionary mapping section types to their prompts

        """
        self.system_prompt = system_prompt
        self.section_prompts = section_prompts

    def get_system_prompt(self) -> str:
        """Get the system prompt.

        Returns:
            System prompt string

        """
        return self.system_prompt

    def get_section_prompt(self, section_type: SectionType, **variables: Any) -> str:
        """Get prompt for a specific section with variable interpolation.

        Args:
            section_type: Type of section to get prompt for
            **variables: Variables to interpolate into the prompt

        Returns:
            Formatted prompt string with variables interpolated

        Raises:
            ConfigurationError: If section type not found or a required variable is missing

        """
        # Convert SectionType enum to string key for lookup
        section_key = section_type.value

        if section_key not in self.section_prompts:
            msg = f"No prompt template found for section type: {section_type}"
            logger.error(msg)
            raise ConfigurationError(
                msg,
                suggestion="Ensure the prompt template file includes a prompt for every SectionType value.",
            )

        prompt_template = self.section_prompts[section_key]

        # Interpolate variables into the template
        try:
            return prompt_template.format(**variables)
        except KeyError as e:
            msg = f"Missing required variable for prompt interpolation: {e}"
            logger.exception(msg)
            raise ConfigurationError(
                msg,
                suggestion="Check that all required template variables are passed when calling get_section_prompt.",
            ) from e


class PromptLoader:
    """Loads and validates prompt templates from YAML files."""

    @staticmethod
    def load_default() -> PromptTemplate:
        """Load default prompt templates bundled with the package.

        Returns:
            PromptTemplate with default prompts

        Raises:
            ConfigurationError: If default templates cannot be loaded

        """
        default_path = Path(__file__).parent / "prompts.yaml"
        return PromptLoader.load_from_file(default_path)

    @staticmethod
    def load_from_file(filepath: Path) -> PromptTemplate:
        """Load prompt templates from a YAML file.

        Args:
            filepath: Path to YAML file containing prompt templates

        Returns:
            PromptTemplate loaded from file

        Raises:
            ConfigurationError: If file doesn't exist, is invalid YAML, or missing required fields

        """
        if not filepath.exists():
            msg = f"Prompt template file not found: {filepath}"
            logger.error(msg)
            raise ConfigurationError(
                msg,
                suggestion="Check the PROMPT_TEMPLATE_PATH environment variable or use default templates",
            )

        try:
            with filepath.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            msg = f"Invalid YAML in prompt template file: {filepath} - {e}"
            logger.exception(msg)
            raise ConfigurationError(
                msg,
                suggestion="Check the YAML syntax in your prompt template file",
            ) from e
        except Exception as e:
            msg = f"Failed to read prompt template file: {filepath} - {e}"
            logger.exception(msg)
            raise ConfigurationError(msg) from e

        # Validate required structure
        if not isinstance(data, dict):
            msg = f"Invalid prompt template format: expected dictionary, got {type(data).__name__}"
            logger.error(msg)
            raise ConfigurationError(
                msg,
                suggestion="Prompt template file must contain a YAML dictionary with 'system_prompt' and 'sections' keys",
            )

        if "system_prompt" not in data:
            msg = "Missing required 'system_prompt' field in prompt template"
            logger.error(msg)
            raise ConfigurationError(
                msg,
                suggestion="Add a 'system_prompt' field to your prompt template file",
            )

        if "sections" not in data or not isinstance(data["sections"], dict):
            msg = "Missing or invalid 'sections' field in prompt template"
            logger.error(msg)
            raise ConfigurationError(
                msg,
                suggestion="Add a 'sections' dictionary to your prompt template file with prompts for each section type",
            )

        # Extract section prompts
        section_prompts = {}
        for section_key, section_data in data["sections"].items():
            if not isinstance(section_data, dict) or "prompt" not in section_data:
                msg = f"Invalid format for section '{section_key}': expected dictionary with 'prompt' key"
                logger.warning(msg)
                continue

            section_prompts[section_key] = section_data["prompt"]

        # Validate that all required section types have prompts
        required_sections = {st.value for st in SectionType}
        missing_sections = required_sections - set(section_prompts.keys())

        if missing_sections:
            msg = f"Missing prompts for required sections: {', '.join(missing_sections)}"
            logger.warning(msg)
            # Don't fail, but warn - users might be testing partial templates

        logger.info(
            "Loaded prompt templates from %s: system_prompt + %d section prompts",
            filepath,
            len(section_prompts),
        )

        return PromptTemplate(
            system_prompt=data["system_prompt"],
            section_prompts=section_prompts,
        )
