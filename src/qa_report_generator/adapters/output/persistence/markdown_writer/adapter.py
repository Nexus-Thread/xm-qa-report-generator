"""Markdown report writer adapter."""

import logging
from pathlib import Path

from qa_report_generator.application.ports.output import NarrativeGenerator, ReportWriter
from qa_report_generator.config import Config
from qa_report_generator.domain.exceptions import PersistenceError
from qa_report_generator.domain.models import ReportFacts
from qa_report_generator.templates import PromptLoader, PromptTemplate

from .renderers import render_pytest_summary, render_signoff_report

logger = logging.getLogger(__name__)


class MarkdownReportWriter(ReportWriter):
    """Writes test reports to markdown files."""

    def __init__(
        self,
        config: Config,
        prompt_template_path: Path | None = None,
    ) -> None:
        """Initialize markdown report writer.

        Args:
            config: Configuration for prompts and parallelism
            prompt_template_path: Optional path to custom prompt templates

        """
        self.prompt_template = self._load_prompt_template(config, prompt_template_path)
        self._active_prompt_path = self._resolve_prompt_path(config, prompt_template_path)

        # Store configuration
        self.max_parallel_sections = config.max_parallel_llm_sections
        self._max_output_lines_per_failure = config.max_output_lines_per_failure
        self._enable_failure_grouping = config.enable_failure_grouping
        self._max_failures_for_detailed_prompt = config.max_failures_for_detailed_prompt

    def save_reports(
        self,
        facts: ReportFacts,
        output_dir: Path,
        narrative_generator: NarrativeGenerator | None = None,
        prompt_template_path: Path | None = None,
    ) -> tuple[Path, Path]:
        """Generate and save both summary and sign-off reports.

        Args:
            facts: Test run facts
            output_dir: Directory to save reports
            narrative_generator: Optional narrative generator for LLM sections
            prompt_template_path: Optional path to custom prompt templates

        Returns:
            Tuple of (summary_path, signoff_path)

        Raises:
            PersistenceError: If writing fails

        """
        logger.info("Saving reports to directory: %s", output_dir)

        # Reload prompt template if a different path is provided
        if prompt_template_path and prompt_template_path != self._active_prompt_path:
            logger.info("Reloading prompt templates from %s", prompt_template_path)
            self.prompt_template = PromptLoader.load_from_file(prompt_template_path)
            self._active_prompt_path = prompt_template_path

        # Create output directory
        self._create_output_directory(output_dir)

        # Generate and write reports
        try:
            summary_path = self._write_summary_report(facts, output_dir, narrative_generator)
            signoff_path = self._write_signoff_report(facts, output_dir, narrative_generator)
        except Exception as e:
            msg = f"Failed to write reports: {e}"
            logger.exception("Failed to write reports: %s", msg)
            raise PersistenceError(msg) from e
        else:
            logger.info("Both reports saved successfully")
            return summary_path, signoff_path

    def _load_prompt_template(self, config: Config, prompt_template_path: Path | None) -> PromptTemplate:
        """Load prompt template from path or use default.

        Args:
            config: Application configuration
            prompt_template_path: Optional custom template path

        Returns:
            Loaded prompt template

        """
        effective_path = self._resolve_prompt_path(config, prompt_template_path)

        if effective_path:
            logger.info("Loading custom prompt templates from: %s", effective_path)
            return PromptLoader.load_from_file(effective_path)
        logger.info("Loading default prompt templates")
        return PromptLoader.load_default()

    def _resolve_prompt_path(self, config: Config, prompt_template_path: Path | None) -> Path | None:
        """Resolve the effective prompt template path."""
        if prompt_template_path is not None:
            return prompt_template_path
        if config.prompt_template_path:
            return Path(config.prompt_template_path)
        return None

    def _create_output_directory(self, output_dir: Path) -> None:
        """Create output directory with error handling.

        Args:
            output_dir: Directory to create

        Raises:
            PersistenceError: If directory creation fails

        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Output directory created/verified: %s", output_dir)
        except (OSError, PermissionError) as e:
            msg = f"Failed to create output directory: {e}"
            logger.exception("Failed to create output directory: %s", msg)
            raise PersistenceError(
                msg,
                suggestion="Check directory permissions and available disk space.",
            ) from e

    def _write_summary_report(
        self,
        facts: ReportFacts,
        output_dir: Path,
        narrative_generator: NarrativeGenerator | None,
    ) -> Path:
        """Generate and write summary report.

        Args:
            facts: Test run facts
            output_dir: Output directory
            narrative_generator: Optional narrative generator

        Returns:
            Path to written summary report

        """
        logger.debug("Rendering pytest summary report")
        summary_md = render_pytest_summary(
            facts=facts,
            narrative_generator=narrative_generator,
            prompt_template=self.prompt_template,
            max_parallel_sections=self.max_parallel_sections,
            max_output_lines=self._max_output_lines_per_failure,
            enable_failure_grouping=self._enable_failure_grouping,
            max_detailed_failures=self._max_failures_for_detailed_prompt,
        )

        summary_path = output_dir / "pytest_summary.md"
        summary_path.write_text(summary_md, encoding="utf-8")
        summary_size = len(summary_md)
        logger.info(
            "Summary report written: %s (%d bytes)",
            summary_path,
            summary_size,
        )

        return summary_path

    def _write_signoff_report(
        self,
        facts: ReportFacts,
        output_dir: Path,
        narrative_generator: NarrativeGenerator | None,
    ) -> Path:
        """Generate and write sign-off report.

        Args:
            facts: Test run facts
            output_dir: Output directory
            narrative_generator: Optional narrative generator

        Returns:
            Path to written sign-off report

        """
        logger.debug("Rendering sign-off report")
        signoff_md = render_signoff_report(
            facts=facts,
            narrative_generator=narrative_generator,
            prompt_template=self.prompt_template,
            max_parallel_sections=self.max_parallel_sections,
            max_output_lines=self._max_output_lines_per_failure,
            enable_failure_grouping=self._enable_failure_grouping,
            max_detailed_failures=self._max_failures_for_detailed_prompt,
        )

        signoff_path = output_dir / "signoff_report.md"
        signoff_path.write_text(signoff_md, encoding="utf-8")
        signoff_size = len(signoff_md)
        logger.info(
            "Sign-off report written: %s (%d bytes)",
            signoff_path,
            signoff_size,
        )

        return signoff_path
