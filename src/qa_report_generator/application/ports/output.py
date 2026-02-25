"""Output ports for external dependencies."""

from abc import ABC, abstractmethod
from pathlib import Path

from qa_report_generator.application.dtos.parsed_report import ParsedReport
from qa_report_generator.application.dtos.section_prompt import SectionPrompt
from qa_report_generator.domain.models import EnvironmentMeta, ReportFacts, RunMetrics
from qa_report_generator.domain.models.k6.context import K6ReportContext


class ReportParser(ABC):
    """Parse test reports from various sources."""

    @abstractmethod
    def parse(self, filepath: Path) -> ParsedReport:
        """Parse test report file and extract metrics and format-specific context."""


class NarrativeGenerator(ABC):
    """Generate narrative report sections."""

    @abstractmethod
    def generate(
        self,
        section_prompt: SectionPrompt,
        user_prompt: str,
    ) -> str | None:
        """Generate narrative content for a report section."""


class ReportWriter(ABC):
    """Write reports to storage."""

    @abstractmethod
    def save_reports(
        self,
        facts: ReportFacts,
        output_dir: Path,
        narrative_generator: NarrativeGenerator | None = None,
        prompt_template_path: Path | None = None,
    ) -> tuple[Path, Path]:
        """Generate and save summary and sign-off reports."""


class ReportCache(ABC):
    """Cache parsed report facts for regeneration workflows."""

    @abstractmethod
    def load_cached_facts(
        self,
        report_path: Path,
    ) -> tuple[RunMetrics, K6ReportContext | None, EnvironmentMeta, list[str]] | None:
        """Load cached facts for a report path."""

    @abstractmethod
    def save_cached_facts(
        self,
        report_path: Path,
        metrics: RunMetrics,
        environment: EnvironmentMeta,
        input_files: list[str],
        k6_context: K6ReportContext | None = None,
    ) -> None:
        """Persist parsed facts for later regeneration."""
