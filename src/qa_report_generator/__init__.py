"""QA Report Generator for LLM-powered test reporting.

This package generates human-readable test reports using LLM narrative generation.
It follows clean architecture principles with clear separation between domain,
application, and infrastructure layers.

Key features:
    - Parse pytest JSON reports
    - Generate AI-powered narrative summaries
    - Output to Markdown format
    - Configure via environment variables
    - Extend via parser/writer plugins

Quick start:
    >>> from pathlib import Path
    >>> from qa_report_generator import (
    ...     EnvironmentMeta,
    ...     MarkdownReportWriter,
    ...     NarrativeAdapter,
    ...     NarrativeAdapterConfig,
    ...     PytestJsonParser,
    ...     ReportGenerationService,
    ... )
    >>> from qa_report_generator.adapters.input.env import EnvSettingsAdapter
    >>> from qa_report_generator.adapters.output.narrative.openai import OpenAIClientSettings, build_client
    >>> config = EnvSettingsAdapter().load()
    >>> narrative_config = NarrativeAdapterConfig(llm_model=config.llm_model)
    >>> openai_settings = OpenAIClientSettings(
    ...     base_url=config.llm_base_url,
    ...     api_key=config.llm_api_key,
    ...     max_retries=config.llm_max_retries,
    ...     backoff_seconds=config.llm_retry_backoff_factor,
    ...     timeout_seconds=config.llm_timeout,
    ... )
    >>> service = ReportGenerationService(
    ...     parser=PytestJsonParser(),
    ...     writer=MarkdownReportWriter(config),
    ...     narrative_generator=NarrativeAdapter(narrative_config, client=build_client(openai_settings)),
    ... )
    >>> result = service.generate(
    ...     report_path=Path("pytest_report.json"),
    ...     output_dir=Path("output"),
    ...     environment=EnvironmentMeta(env="staging"),
    ... )
    >>> result.summary_path
    PosixPath('output/test_summary.md')

CLI usage:
    $ python -m qa_report_generator generate --json-report pytest_report.json --out output/
"""

__version__ = "0.1.0"

from qa_report_generator.adapters import CliAdapter, MarkdownReportWriter, NarrativeAdapter, PytestJsonParser
from qa_report_generator.adapters.output.narrative import NarrativeAdapterConfig
from qa_report_generator.application import ReportGenerationService
from qa_report_generator.domain import (
    Duration,
    EnvironmentMeta,
    Failure,
    PassRate,
    ReportFacts,
    RunMetrics,
    TestIdentifier,
    TestStatus,
)

__all__ = [
    "CliAdapter",
    "Duration",
    "EnvironmentMeta",
    "Failure",
    "MarkdownReportWriter",
    "NarrativeAdapter",
    "NarrativeAdapterConfig",
    "PassRate",
    "PytestJsonParser",
    "ReportFacts",
    "ReportGenerationService",
    "RunMetrics",
    "TestIdentifier",
    "TestStatus",
    "__version__",
]
