"""Composition root: wires all adapters, use cases, and configuration into the CLI."""

from pathlib import Path

from qa_report_generator.adapters.input.cli_adapter import CliAdapter
from qa_report_generator.adapters.input.env import EnvSettingsAdapter
from qa_report_generator.adapters.output.narrative import NarrativeAdapter, NarrativeAdapterConfig
from qa_report_generator.adapters.output.narrative.openai import OpenAIClientSettings, build_client
from qa_report_generator.adapters.output.parsers import K6JsonParser, K6SummaryTableParser, PytestJsonParser
from qa_report_generator.adapters.output.persistence.cache import FileReportCache
from qa_report_generator.adapters.output.persistence.markdown_writer import MarkdownReportWriter
from qa_report_generator.adapters.output.persistence.performance import K6SummaryTableMarkdownWriter
from qa_report_generator.application.use_cases import (
    K6SummaryTableService,
    ReportComparisonService,
    ReportGenerationService,
    ReportValidationService,
)
from qa_report_generator.config import setup_logging
from qa_report_generator.plugins import discover_plugins


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

    # Setup logging based on business configuration
    setup_logging(config)

    # Load plugin entry points and optional modules before wiring adapters
    discover_plugins(config.plugin_modules)

    # Create output adapters (driven side)
    parsers = {
        "pytest": PytestJsonParser(),
        "k6": K6JsonParser(),
    }
    writer = MarkdownReportWriter(config)  # Handles prompts (business logic)

    # Build OpenAI transport and narrative adapter explicitly
    narrative_config = NarrativeAdapterConfig(llm_model=config.llm_model)
    openai_settings = OpenAIClientSettings(
        base_url=config.llm_base_url,
        api_key=config.llm_api_key,
        max_retries=config.llm_max_retries,
        backoff_seconds=config.llm_retry_backoff_factor,
        timeout_seconds=config.llm_timeout,
    )
    narrative_generator = NarrativeAdapter(narrative_config, client=build_client(openai_settings))
    cache = FileReportCache(Path(".cache"))

    # Create use case with dependencies
    report_use_case = ReportGenerationService(
        parsers=parsers,
        writer=writer,
        narrative_generator=narrative_generator,
        failure_clustering_threshold=config.failure_clustering_threshold,
        report_cache=cache,
    )
    k6_summary_table_use_case = K6SummaryTableService(
        parser=K6SummaryTableParser(),
        writer=K6SummaryTableMarkdownWriter(),
    )
    compare_use_case = ReportComparisonService(parsers)
    validate_use_case = ReportValidationService(parsers)

    # Create and return CLI adapter (driving side)
    return CliAdapter(
        generate_reports_use_case=report_use_case,
        generate_k6_summary_table_use_case=k6_summary_table_use_case,
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
