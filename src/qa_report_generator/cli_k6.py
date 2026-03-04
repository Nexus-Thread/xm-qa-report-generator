"""Composition root for the k6-only CLI."""

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.adapters.input.env import EnvSettingsAdapter
from qa_report_generator.adapters.output.narrative.openai import OpenAIClientSettings, build_client
from qa_report_generator.adapters.output.narrative.structured_llm import OpenAIStructuredLlmAdapter
from qa_report_generator.adapters.output.parsers import K6ParsedReportParser
from qa_report_generator.adapters.output.persistence import JsonFileDebugWriterAdapter
from qa_report_generator.application.use_cases import (
    K6ServiceExtractionService,
)
from qa_report_generator.config import setup_logging


def create_cli_adapter() -> K6CliAdapter:
    """Create a k6-only CLI adapter with dependencies wired."""
    config = EnvSettingsAdapter().load()

    setup_logging(config)

    openai_client = build_client(
        OpenAIClientSettings(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            max_retries=config.llm_max_retries,
            backoff_factor=config.llm_retry_backoff_factor,
            timeout_seconds=config.llm_timeout,
        )
    )
    debug_json_writer = JsonFileDebugWriterAdapter(base_dir=config.llm_debug_json_dir)
    structured_llm = OpenAIStructuredLlmAdapter(
        client=openai_client,
        model=config.llm_model,
        debug_json_writer=debug_json_writer,
        debug_json_enabled=config.llm_debug_json_enabled,
    )
    parsed_report_parser = K6ParsedReportParser()
    k6_service_extraction_use_case = K6ServiceExtractionService(llm=structured_llm, parser=parsed_report_parser)

    return K6CliAdapter(
        extract_k6_service_metrics_use_case=k6_service_extraction_use_case,
    )


def main() -> None:
    """Run the k6-only CLI application."""
    cli = create_cli_adapter()
    cli.run()


if __name__ == "__main__":
    main()
