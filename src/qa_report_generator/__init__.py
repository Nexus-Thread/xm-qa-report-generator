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
    ...     LLMAdapterConfig,
    ...     MarkdownReportWriter,
    ...     NarrativeAdapter,
    ...     PytestJsonParser,
    ...     ReportGenerationService,
    ... )
    >>> from qa_report_generator.adapters.input.env import EnvSettingsAdapter
    >>> from qa_report_generator.adapters.output.narrative.openai import build_client
    >>> config = EnvSettingsAdapter().load()
    >>> llm_config = LLMAdapterConfig(
    ...     llm_model=config.llm_model,
    ...     llm_base_url=config.llm_base_url,
    ...     llm_api_key=config.llm_api_key,
    ...     llm_temperature=config.llm_temperature,
    ...     llm_reasoning_effort=config.llm_reasoning_effort,
    ...     llm_timeout=config.llm_timeout,
    ...     llm_max_retries=config.llm_max_retries,
    ...     llm_retry_backoff_factor=config.llm_retry_backoff_factor,
    ... )
    >>> service = ReportGenerationService(
    ...     parser=PytestJsonParser(),
    ...     writer=MarkdownReportWriter(config),
    ...     narrative_generator=NarrativeAdapter(llm_config, client=build_client(llm_config)),
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
from qa_report_generator.adapters.output.narrative import LLMAdapterConfig
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
    "LLMAdapterConfig",
    "MarkdownReportWriter",
    "NarrativeAdapter",
    "PassRate",
    "PytestJsonParser",
    "ReportFacts",
    "ReportGenerationService",
    "RunMetrics",
    "TestIdentifier",
    "TestStatus",
    "__version__",
]
