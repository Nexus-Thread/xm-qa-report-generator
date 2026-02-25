"""Application use cases."""

import logging
import time
from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path

from qa_report_generator.application.dtos import SectionPrompt
from qa_report_generator.application.ports.input import (
    CompareReportsUseCase,
    GenerateReportsUseCase,
    ReportGenerationResult,
    ValidateReportUseCase,
)
from qa_report_generator.application.ports.output import (
    NarrativeGenerator,
    ReportCache,
    ReportParser,
    ReportWriter,
)
from qa_report_generator.application.strategies import PromptStrategySelector
from qa_report_generator.domain.analytics.models import ReportDiff
from qa_report_generator.domain.analytics.orchestrator import AnalyticsOrchestrator
from qa_report_generator.domain.analytics.report_diff import diff_runs
from qa_report_generator.domain.exceptions import ConfigurationError, ParseError, ReportingError
from qa_report_generator.domain.models import EnvironmentMeta, ReportFacts, RunMetrics
from qa_report_generator.domain.models.k6 import K6ReportContext
from qa_report_generator.domain.value_objects import SectionType

logger = logging.getLogger(__name__)


class TimedNarrativeGenerator(NarrativeGenerator):
    """Wrap a narrative generator to capture timings."""

    def __init__(self, delegate: NarrativeGenerator) -> None:
        """Initialize the timing wrapper."""
        self._delegate = delegate
        self._durations: dict[SectionType, float] = defaultdict(float)

    def generate(
        self,
        section_prompt: SectionPrompt,
        user_prompt: str,
    ) -> str | None:
        """Generate a narrative section and record duration."""
        start_time = time.time()
        try:
            return self._delegate.generate(
                section_prompt=section_prompt,
                user_prompt=user_prompt,
            )
        finally:
            duration = time.time() - start_time
            self._durations[section_prompt.section_type] += duration
            logger.info(
                "LLM section timing: section=%s duration=%.2fs",
                section_prompt.section_type.value,
                duration,
                extra={
                    "extra_fields": {
                        "section": section_prompt.section_type.value,
                        "duration_seconds": round(duration, 2),
                    },
                },
            )

    @property
    def total_duration(self) -> float:
        """Total elapsed time for all generated sections."""
        return sum(self._durations.values())

    @property
    def section_durations(self) -> dict[SectionType, float]:
        """Elapsed time per section type."""
        return dict(self._durations)


class ReportGenerationService(GenerateReportsUseCase):
    """Generate reports from parsed test results."""

    def __init__(  # noqa: PLR0913
        self,
        parsers: Mapping[str, ReportParser],
        writer: ReportWriter,
        narrative_generator: NarrativeGenerator | None = None,
        prompt_strategy_selector: PromptStrategySelector | None = None,
        failure_clustering_threshold: float = 0.7,
        report_cache: ReportCache | None = None,
    ) -> None:
        """Initialize the report generation service."""
        self._parsers = parsers
        self._writer = writer
        self._narrative_generator = narrative_generator
        self._prompt_strategy_selector = prompt_strategy_selector or PromptStrategySelector()
        self._analytics_orchestrator = AnalyticsOrchestrator()
        self._failure_clustering_threshold = failure_clustering_threshold
        self._report_cache = report_cache

    def generate(  # noqa: PLR0913
        self,
        report_path: Path,
        output_dir: Path,
        environment: EnvironmentMeta,
        report_format: str,
        max_failures: int | None = 20,
        enable_llm: bool = True,
        regenerate_narratives: bool = False,
    ) -> ReportGenerationResult:
        """Generate reports from a test report.

        Args:
            report_path: Path to test report file
            output_dir: Directory to save generated reports
            environment: Environment metadata
            report_format: Source report format identifier (e.g. "pytest", "k6")
            max_failures: Maximum number of failures to include in reports
                (set to None to disable limiting)
            enable_llm: Whether to enable LLM-generated narrative sections
            regenerate_narratives: Use cached parsed facts when available

        Returns:
            ReportGenerationResult with output paths and timing metrics

        Raises:
            ConfigurationError: If the requested report_format is not registered
            ParseError: If input report parsing fails
            ReportingError: If report generation fails

        """
        parser = self._get_parser(report_format)
        start_time = time.time()
        logger.info(
            "Starting report generation workflow: input=%s, output=%s, format=%s, llm_enabled=%s",
            report_path,
            output_dir,
            report_format,
            enable_llm,
        )

        try:
            logger.debug("Step 1: Parsing input report")
            metrics, k6_context, input_files, parse_duration = self._load_or_parse_metrics(
                parser=parser,
                report_path=report_path,
                environment=environment,
                regenerate_narratives=regenerate_narratives,
            )
            logger.debug("Parsing completed in %.2f seconds", parse_duration)

            limited_metrics = self._limit_failures(metrics, max_failures)
            facts = self._build_report_facts(
                metrics=limited_metrics,
                k6_context=k6_context,
                environment=environment,
                input_files=input_files,
                report_format=report_format,
            )

            narrative_generator, timed_narrative_generator = self._prepare_narrative_generator(
                enable_llm,
            )
            prompt_template_path = self._prompt_strategy_selector.select(
                facts.metrics,
            ).template_path

            # Generate and save reports
            logger.debug("Step 3: Generating and saving reports")
            write_start = time.time()
            summary_path, signoff_path = self._writer.save_reports(
                facts=facts,
                output_dir=output_dir,
                narrative_generator=narrative_generator,
                prompt_template_path=prompt_template_path,
            )
            write_duration = time.time() - write_start
            logger.debug("Report writing completed in %.2f seconds", write_duration)

        except (ConfigurationError, ParseError):
            raise
        except ReportingError:
            raise
        except Exception as e:
            msg = f"Failed to generate reports from {report_path}: {type(e).__name__}: {e}"
            logger.exception("Report generation failed: %s", msg)
            raise ReportingError(
                msg,
                suggestion="Check that the input file matches the selected format and the output directory is writable.",
            ) from e
        else:
            total_duration = time.time() - start_time
            llm_duration = timed_narrative_generator.total_duration if timed_narrative_generator else 0.0
            logger.info(
                "Report generated in %.2fs (parse: %.2fs, llm: %.2fs, write: %.2fs)",
                total_duration,
                parse_duration,
                llm_duration,
                write_duration,
                extra={
                    "extra_fields": {
                        "parse_duration_seconds": round(parse_duration, 2),
                        "llm_duration_seconds": round(llm_duration, 2),
                        "write_duration_seconds": round(write_duration, 2),
                        "total_duration_seconds": round(total_duration, 2),
                    },
                },
            )
            logger.info(
                "Report generation completed successfully in %.2f seconds: summary=%s, signoff=%s",
                total_duration,
                summary_path,
                signoff_path,
            )
            return ReportGenerationResult(
                summary_path=summary_path,
                signoff_path=signoff_path,
                parse_duration=parse_duration,
                write_duration=write_duration,
                total_duration=total_duration,
            )

    def _get_parser(self, report_format: str) -> ReportParser:
        """Resolve parser for the given format.

        Args:
            report_format: Format identifier

        Raises:
            ConfigurationError: If format is not registered

        """
        parser = self._parsers.get(report_format)
        if parser is None:
            available = ", ".join(sorted(self._parsers.keys()))
            msg = f"Unknown report format '{report_format}'. Registered formats: {available}"
            raise ConfigurationError(msg, suggestion=f"Use one of: {available}")
        return parser

    def _load_or_parse_metrics(
        self,
        *,
        parser: ReportParser,
        report_path: Path,
        environment: EnvironmentMeta,
        regenerate_narratives: bool,
    ) -> tuple[RunMetrics, K6ReportContext | None, list[str], float]:
        parse_start = time.time()
        cached_facts = None
        if regenerate_narratives and self._report_cache:
            cached_facts = self._report_cache.load_cached_facts(report_path)

        if cached_facts:
            metrics, k6_context, cached_environment, input_files = cached_facts
            if cached_environment != environment:
                logger.warning(
                    "Cached environment differs from current run; using cached facts for regeneration.",
                )
            return metrics, k6_context, input_files, 0.0

        parsed = parser.parse(report_path)
        input_files = [str(report_path)]
        parse_duration = time.time() - parse_start
        if self._report_cache:
            self._report_cache.save_cached_facts(
                report_path=report_path,
                metrics=parsed.metrics,
                environment=environment,
                input_files=input_files,
                k6_context=parsed.k6_context,
            )
        return parsed.metrics, parsed.k6_context, input_files, parse_duration

    def _limit_failures(self, metrics: RunMetrics, max_failures: int | None) -> RunMetrics:
        if max_failures is None:
            return metrics

        original_failure_count = len(metrics.failures)
        limited_metrics = metrics.limit_failures(max_failures)
        if original_failure_count > max_failures:
            logger.info(
                "Limited failures from %d to %d",
                original_failure_count,
                len(limited_metrics.failures),
            )
        return limited_metrics

    def _build_report_facts(
        self,
        *,
        metrics: RunMetrics,
        k6_context: K6ReportContext | None,
        environment: EnvironmentMeta,
        input_files: list[str],
        report_format: str,
    ) -> ReportFacts:
        logger.debug("Step 2: Building report facts")
        facts = self._analytics_orchestrator.build_report_facts(
            metrics=metrics,
            environment=environment,
            input_files=input_files,
            failure_clustering_threshold=self._failure_clustering_threshold,
            source_format=report_format,
            k6_context=k6_context,
        )
        return facts.model_copy(update={"source_format": report_format})

    def _prepare_narrative_generator(
        self,
        enable_llm: bool,
    ) -> tuple[NarrativeGenerator | None, TimedNarrativeGenerator | None]:
        if not enable_llm:
            logger.info("LLM narrative generation disabled")
            return None, None

        if not self._narrative_generator:
            logger.warning("LLM requested but narrative generator not configured")
            return None, None

        logger.info("LLM narrative generation enabled")
        timed_generator = TimedNarrativeGenerator(self._narrative_generator)
        return timed_generator, timed_generator


class ReportComparisonService(CompareReportsUseCase):
    """Compare reports and return a diff summary."""

    def __init__(self, parsers: Mapping[str, ReportParser]) -> None:
        """Initialize the comparison service."""
        self._parsers = parsers

    def compare(self, report_a: Path, report_b: Path, report_format: str) -> ReportDiff:
        """Compare two reports and return a diff summary."""
        parser = self._get_parser(report_format)
        parsed_a = parser.parse(report_a)
        parsed_b = parser.parse(report_b)
        return diff_runs(parsed_a.metrics, parsed_b.metrics)

    def _get_parser(self, report_format: str) -> ReportParser:
        parser = self._parsers.get(report_format)
        if parser is None:
            available = ", ".join(sorted(self._parsers.keys()))
            msg = f"Unknown report format '{report_format}'. Registered formats: {available}"
            raise ConfigurationError(msg, suggestion=f"Use one of: {available}")
        return parser


class ReportValidationService(ValidateReportUseCase):
    """Validate a report by parsing it through the configured parser."""

    def __init__(self, parsers: Mapping[str, ReportParser]) -> None:
        """Initialize the validation service."""
        self._parsers = parsers

    def validate_report(self, report_path: Path, report_format: str) -> RunMetrics:
        """Validate report structure and return parsed metrics."""
        parser = self._parsers.get(report_format)
        if parser is None:
            available = ", ".join(sorted(self._parsers.keys()))
            msg = f"Unknown report format '{report_format}'. Registered formats: {available}"
            raise ConfigurationError(msg, suggestion=f"Use one of: {available}")
        return parser.parse(report_path).metrics
