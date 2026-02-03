"""Example JSON report writer plugin.

This demonstrates how to create a custom writer that outputs reports
in JSON format instead of markdown.

Usage:
    from examples.custom_writer.json_writer import JSONReportWriter
    from qa_report_generator.plugins import WriterRegistry

    # The @register_writer decorator automatically registers it
    writer_class = WriterRegistry.get("json")
    writer = writer_class()
"""

import json
import logging
from pathlib import Path

from qa_report_generator.application.ports.output import NarrativeGenerator, ReportWriter
from qa_report_generator.domain.exceptions import PersistenceError
from qa_report_generator.domain.models import ReportFacts
from qa_report_generator.domain.value_objects import SectionType
from qa_report_generator.plugins import register_writer
from qa_report_generator.templates import PromptLoader, PromptTemplate

logger = logging.getLogger(__name__)


@register_writer("json")
class JSONReportWriter(ReportWriter):
    """Writer that generates JSON format reports."""

    def save_reports(
        self,
        facts: ReportFacts,
        output_dir: Path,
        narrative_generator: NarrativeGenerator | None = None,
        prompt_template_path: Path | None = None,
    ) -> tuple[Path, Path]:
        """Generate and save JSON reports.

        Args:
            facts: Test run facts
            output_dir: Directory to save reports
            narrative_generator: Optional narrative generator for LLM sections
            prompt_template_path: Optional prompt template path for narrative prompts

        Returns:
            Tuple of (summary_path, signoff_path)

        Raises:
            PersistenceError: If writing fails

        """
        logger.info("Saving JSON reports to directory: %s", output_dir)
        prompt_template = self._load_prompt_template(prompt_template_path)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            msg = f"Failed to create output directory: {e}"
            logger.exception(msg)
            raise PersistenceError(msg) from e

        try:
            # Generate summary report JSON
            summary_data = self._create_summary_data(
                facts,
                narrative_generator,
                prompt_template,
            )
            summary_path = output_dir / "pytest_summary.json"

            with summary_path.open("w", encoding="utf-8") as f:
                json.dump(summary_data, f, indent=2)

            logger.info("JSON summary report written: %s", summary_path)

            # Generate sign-off report JSON
            signoff_data = self._create_signoff_data(
                facts,
                narrative_generator,
                prompt_template,
            )
            signoff_path = output_dir / "signoff_report.json"

            with signoff_path.open("w", encoding="utf-8") as f:
                json.dump(signoff_data, f, indent=2)

            logger.info("JSON sign-off report written: %s", signoff_path)

        except Exception as e:
            msg = f"Failed to write JSON reports: {e}"
            logger.exception(msg)
            raise PersistenceError(msg) from e
        else:
            return summary_path, signoff_path

    def _create_summary_data(
        self,
        facts: ReportFacts,
        narrative_generator: NarrativeGenerator | None,
        prompt_template: PromptTemplate | None,
    ) -> dict:
        """Create summary report data structure.

        Args:
            facts: Test run facts
            narrative_generator: Optional LLM generator
            prompt_template: Optional prompt template for narrative generation

        Returns:
            Dictionary containing report data

        """
        data = {
            "report_type": "pytest_summary",
            "generated_at": facts.timestamp_iso,
            "metrics": {
                "total": facts.metrics.total,
                "passed": facts.metrics.passed,
                "failed": facts.metrics.failed,
                "skipped": facts.metrics.skipped,
                "errors": facts.metrics.errors,
                "duration_seconds": facts.metrics.duration_seconds,
                "pass_rate": facts.metrics.pass_rate.formatted,
            },
            "environment": {
                "env": facts.environment.env,
                "build": facts.environment.build,
                "commit": facts.environment.commit,
                "target_url": facts.environment.target_url,
            },
            "narratives": {},
            "failures": [],
            "input_files": facts.input_files,
        }

        # Add LLM-generated narratives if available
        if narrative_generator and prompt_template:
            data["narratives"]["executive_summary"] = (
                self._generate_narrative(
                    facts,
                    narrative_generator,
                    prompt_template,
                    SectionType.EXECUTIVE_SUMMARY,
                )
                or "N/A"
            )
            data["narratives"]["key_observations"] = (
                self._generate_narrative(
                    facts,
                    narrative_generator,
                    prompt_template,
                    SectionType.KEY_OBSERVATIONS,
                )
                or "N/A"
            )
        else:
            data["narratives"]["note"] = "LLM disabled"

        # Add failure details (limit to 20)
        for failure in facts.metrics.failures[:20]:
            failure_data = {
                "test_name": failure.test_name,
                "suite": failure.suite,
                "type": failure.type,
                "message": failure.message,
                "duration": failure.duration.formatted if failure.duration else None,
            }

            if failure.output:
                failure_data["output"] = {
                    "stdout": failure.output.stdout,
                    "stderr": failure.output.stderr,
                    "log": failure.output.log,
                }

            data["failures"].append(failure_data)

        return data

    def _create_signoff_data(
        self,
        facts: ReportFacts,
        narrative_generator: NarrativeGenerator | None,
        prompt_template: PromptTemplate | None,
    ) -> dict:
        """Create sign-off report data structure.

        Args:
            facts: Test run facts
            narrative_generator: Optional LLM generator
            prompt_template: Optional prompt template for narrative generation

        Returns:
            Dictionary containing report data

        """
        data = {
            "report_type": "qa_signoff",
            "generated_at": facts.timestamp_iso,
            "metrics": {
                "total": facts.metrics.total,
                "passed": facts.metrics.passed,
                "failed": facts.metrics.failed,
                "pass_rate": facts.metrics.pass_rate.formatted,
            },
            "narratives": {},
            "critical_failures": [],
            "signoff": {
                "qa_engineer": None,
                "date": None,
                "approved": None,
            },
            "input_files": facts.input_files,
        }

        # Add LLM-generated narratives if available
        if narrative_generator and prompt_template:
            data["narratives"]["risk_assessment"] = (
                self._generate_narrative(
                    facts,
                    narrative_generator,
                    prompt_template,
                    SectionType.RISK_ASSESSMENT,
                )
                or "N/A"
            )
            data["narratives"]["recommendation"] = (
                self._generate_narrative(
                    facts,
                    narrative_generator,
                    prompt_template,
                    SectionType.RECOMMENDATION,
                )
                or "N/A"
            )
        else:
            data["narratives"]["note"] = "LLM disabled"

        # Add critical failures (limit to 10)
        for failure in facts.metrics.failures[:10]:
            data["critical_failures"].append(
                {
                    "test_name": failure.test_name,
                    "suite": failure.suite,
                    "message": failure.message[:200],  # Truncate for signoff
                }
            )

        return data

    def _load_prompt_template(
        self,
        prompt_template_path: Path | None,
    ) -> PromptTemplate | None:
        if not prompt_template_path:
            return None

        logger.info("Loading prompt templates from: %s", prompt_template_path)
        return PromptLoader.load_from_file(prompt_template_path)

    def _generate_narrative(
        self,
        facts: ReportFacts,
        narrative_generator: NarrativeGenerator,
        prompt_template: PromptTemplate,
        section_type: SectionType,
    ) -> str | None:
        try:
            facts_json = json.dumps(facts.to_dict(), indent=2)
        except (TypeError, ValueError) as e:
            msg = f"Failed to serialize report facts for LLM prompts: {e}"
            logger.exception(msg)
            raise PersistenceError(
                msg,
                suggestion="Ensure report facts contain only JSON-serializable values.",
            ) from e

        system_prompt = prompt_template.get_system_prompt()
        user_prompt = prompt_template.get_section_prompt(section_type, facts_json=facts_json)
        return narrative_generator.generate(section_type, system_prompt, user_prompt)
