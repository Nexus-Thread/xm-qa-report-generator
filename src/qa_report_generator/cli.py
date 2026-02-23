"""Composition root: wires all adapters, use cases, and configuration into the CLI."""

from pathlib import Path

from qa_report_generator.adapters.input.cli_adapter import CliAdapter
from qa_report_generator.adapters.input.env import EnvSettingsAdapter
from qa_report_generator.adapters.output.narrative import LLMAdapter, LLMAdapterConfig
from qa_report_generator.adapters.output.parsers import PytestJsonParser
from qa_report_generator.adapters.output.persistence.cache import FileReportCache
from qa_report_generator.adapters.output.persistence.markdown_writer import MarkdownReportWriter
from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.application.use_cases import (
    ReportComparisonService,
    ReportGenerationService,
    ReportValidationService,
)
from qa_report_generator.logging_config import setup_logging
from qa_report_generator.plugins import discover_plugins


def _build_llm_adapter_config(config: AppSettings) -> LLMAdapterConfig:
    """Build technical LLM adapter settings from application config."""
    return LLMAdapterConfig(
        llm_model=config.llm_model,
        llm_base_url=config.llm_base_url,
        llm_api_key=config.llm_api_key,
        llm_temperature=config.llm_temperature,
        llm_reasoning_effort=config.llm_reasoning_effort,
        llm_timeout=config.llm_timeout,
        llm_max_retries=config.llm_max_retries,
        llm_retry_backoff_factor=config.llm_retry_backoff_factor,
    )


def create_cli_adapter() -> CliAdapter:
    """Create a CLI adapter with all dependencies wired together.

    This function serves as the composition root for dependency injection,
    meaning it's the single place where all objects are instantiated and
    connected. This centralizes dependency management and makes the
    application easier to test and modify.

    The wiring follows clean-architecture layers:
    1. Infrastructure: create all adapters (parsers, writers, LLM, configs)
    2. Application: wire adapters into the use case (business logic)
    3. Interface: return the CLI adapter (user-facing entry point)

    Returns:
        Fully configured CLI adapter ready to handle user commands.

    """
    # Load configuration directly from environment (composition root — infrastructure layer)
    config = EnvSettingsAdapter().load()
    llm_config = _build_llm_adapter_config(config)

    # Setup logging based on business configuration
    setup_logging(config)

    # Load plugin entry points and optional modules before wiring adapters
    discover_plugins(config.plugin_modules)

    # Create output adapters (driven side)
    parser = PytestJsonParser()
    writer = MarkdownReportWriter(config)  # Handles prompts (business logic)
    narrative_generator = LLMAdapter(llm_config)  # Pure technical adapter
    cache = FileReportCache(Path(".cache"))

    # Create use case with dependencies
    report_use_case = ReportGenerationService(
        parser=parser,
        writer=writer,
        narrative_generator=narrative_generator,
        failure_clustering_threshold=config.failure_clustering_threshold,
        report_cache=cache,
    )
    compare_use_case = ReportComparisonService(parser)
    validate_use_case = ReportValidationService(parser)

    # Create and return CLI adapter (driving side)
    return CliAdapter(
        generate_reports_use_case=report_use_case,
        compare_reports_use_case=compare_use_case,
        validate_report_use_case=validate_use_case,
        config=config,
    )


def main() -> None:
    """Run the CLI application."""
    cli = create_cli_adapter()
    cli.run()


if __name__ == "__main__":
    main()
