"""Composition root for the k6-only CLI."""

import logging

import typer

from qa_report_generator_performance.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator_performance.adapters.input.env_settings_adapter import EnvSettingsAdapter
from qa_report_generator_performance.adapters.output.parsers import K6ParsedReportParser
from qa_report_generator_performance.adapters.output.structured_llm_adapter import OpenAILlmUsageTracker, StructuredLlmPortAdapter
from qa_report_generator_performance.application.use_cases import (
    K6ServiceExtractionDebugConfig,
    K6ServiceExtractionRuntimeConfig,
    K6ServiceExtractionService,
)
from qa_report_generator_performance.config import setup_logging
from shared.adapters.output.llm import OpenAIClientSettings, OpenAIStructuredLlmAdapter, build_client
from shared.adapters.output.persistence import JsonFileWriterAdapter

LOGGER = logging.getLogger(__name__)


def create_cli_adapter() -> K6CliAdapter:
    """Create a k6-only CLI adapter with dependencies wired."""
    config = EnvSettingsAdapter().load()

    setup_logging(config)
    LOGGER.info(
        "Application logging configured",
        extra={
            "component": "cli",
            "log_level": config.log_level,
            "log_format": config.log_format,
            "llm_model": config.llm_model,
            "llm_base_url": config.llm_base_url,
            "llm_timeout_seconds": config.llm_timeout,
            "llm_max_retries": config.llm_max_retries,
            "llm_max_concurrency": config.llm_max_concurrency,
            "llm_debug_json_enabled": config.llm_debug_json_enabled,
            "model_debug_json_enabled": config.model_debug_json_enabled,
        },
    )
    if config.llm_debug_json_enabled:
        LOGGER.info(
            "Structured LLM debug JSON output enabled",
            extra={
                "component": "cli",
                "debug_output": "llm",
                "debug_json_dir": str(config.llm_debug_json_dir),
            },
        )
    if config.model_debug_json_enabled:
        LOGGER.info(
            "Model debug JSON output enabled",
            extra={
                "component": "cli",
                "debug_output": "model",
                "debug_json_dir": str(config.model_debug_json_dir),
            },
        )

    openai_client = build_client(
        OpenAIClientSettings(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            max_retries=config.llm_max_retries,
            backoff_factor=config.llm_retry_backoff_factor,
            timeout_seconds=config.llm_timeout,
        )
    )
    debug_json_writer = JsonFileWriterAdapter(base_dir=config.llm_debug_json_dir)
    model_debug_json_writer = JsonFileWriterAdapter(base_dir=config.model_debug_json_dir)
    usage_tracker = OpenAILlmUsageTracker(
        input_cost_per_million_tokens=config.llm_input_cost_per_million_tokens,
        output_cost_per_million_tokens=config.llm_output_cost_per_million_tokens,
    )
    structured_llm_adapter = OpenAIStructuredLlmAdapter(
        client=openai_client,
        model=config.llm_model,
        debug_json_writer=debug_json_writer,
        debug_json_enabled=config.llm_debug_json_enabled,
    )
    structured_llm = StructuredLlmPortAdapter(adapter=structured_llm_adapter, usage_tracker=usage_tracker)
    parsed_report_parser = K6ParsedReportParser()
    service_metrics_extractor = K6ServiceExtractionService(
        llm=structured_llm,
        parser=parsed_report_parser,
        runtime_config=K6ServiceExtractionRuntimeConfig(
            llm_usage_summary_provider=usage_tracker,
            max_parallel_scenarios=config.llm_max_concurrency,
        ),
        debug_config=K6ServiceExtractionDebugConfig(
            model_debug_json_writer=model_debug_json_writer,
            model_debug_json_enabled=config.model_debug_json_enabled,
        ),
    )

    return K6CliAdapter(
        service_metrics_extractor=service_metrics_extractor,
    )


def main() -> None:
    """Run the k6-only CLI application."""
    cli = create_cli_adapter()
    try:
        cli.run()
    except typer.Exit:
        raise
    except Exception:
        LOGGER.exception(
            "CLI execution terminated unexpectedly",
            extra={"component": "cli"},
        )
        raise


if __name__ == "__main__":
    main()
