"""Report rendering logic for summary and sign-off reports."""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from qa_report_generator.application.dtos import SectionPrompt
from qa_report_generator.application.ports.output import NarrativeGenerator
from qa_report_generator.domain.exceptions import PersistenceError
from qa_report_generator.domain.models import ReportFacts
from qa_report_generator.domain.value_objects import SectionType
from qa_report_generator.templates import PromptTemplate

from .formatters import (
    format_artifacts_section,
    format_engineering_summary,
    format_facts_table,
    format_failures,
    format_generated_section,
    format_k6_scenario_load_model_overview,
    format_quick_stats_card,
)
from .serializers import build_llm_facts_payload

logger = logging.getLogger(__name__)


_SUMMARY_TITLES: dict[str, str] = {
    "pytest": "Pytest Run Summary",
    "k6": "K6 Load Test Summary",
}
_SIGNOFF_TITLES: dict[str, str] = {
    "pytest": "QA Sign-Off Report",
    "k6": "K6 Performance Sign-Off Report",
}


def render_pytest_summary(  # noqa: PLR0913
    facts: ReportFacts,
    narrative_generator: NarrativeGenerator | None,
    prompt_template: PromptTemplate,
    max_parallel_sections: int,
    max_output_lines: int,
    enable_failure_grouping: bool,
    max_detailed_failures: int,
) -> str:
    """Render test run summary report.

    Args:
        facts: Test run facts
        narrative_generator: Optional narrative generator
        prompt_template: Prompt template for LLM sections
        max_parallel_sections: Maximum parallel LLM calls
        max_output_lines: Maximum output lines per failure
        enable_failure_grouping: Whether to group failures
        max_detailed_failures: Maximum failures in detailed payload

    Returns:
        Markdown content

    """
    md_parts = []

    # Header
    title = _SUMMARY_TITLES.get(facts.source_format, _SUMMARY_TITLES["pytest"])
    md_parts.append(f"# {title}\n")
    md_parts.append(f"*Generated: {facts.timestamp_iso}*\n")

    # Quick stats card
    md_parts.append(format_quick_stats_card(facts))

    # Deterministic: Run Facts
    md_parts.append("## Run Facts\n")
    md_parts.append(format_facts_table(facts))

    if facts.source_format == "k6":
        md_parts.append("## Scenario & Load Model\n")
        md_parts.append(format_k6_scenario_load_model_overview(facts))

    generated_sections = _generate_llm_sections(
        facts=facts,
        narrative_generator=narrative_generator,
        section_types=[
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.KEY_OBSERVATIONS,
        ],
        prompt_template=prompt_template,
        max_parallel_sections=max_parallel_sections,
        max_output_lines=max_output_lines,
        enable_failure_grouping=enable_failure_grouping,
        max_detailed_failures=max_detailed_failures,
    )

    # LLM: Executive Summary
    md_parts.append("## Executive Summary\n")
    md_parts.append(format_generated_section(generated_sections.get(SectionType.EXECUTIVE_SUMMARY)))

    # LLM: Key Observations
    md_parts.append("## Key Observations\n")
    md_parts.append(format_generated_section(generated_sections.get(SectionType.KEY_OBSERVATIONS)))

    # Deterministic: Engineering Summary
    md_parts.append("## Engineering Summary\n")
    md_parts.append(format_engineering_summary(facts))

    # Deterministic: Top Failures
    md_parts.append("## Top Failures\n")
    md_parts.append(format_failures(facts, max_failures=20, max_output_lines=max_output_lines))

    # Footer: Input artifacts
    md_parts.append(format_artifacts_section(facts))

    return "\n".join(md_parts)


def render_signoff_report(  # noqa: PLR0913
    facts: ReportFacts,
    narrative_generator: NarrativeGenerator | None,
    prompt_template: PromptTemplate,
    max_parallel_sections: int,
    max_output_lines: int,
    enable_failure_grouping: bool,
    max_detailed_failures: int,
) -> str:
    """Render QA sign-off report.

    Args:
        facts: Test run facts
        narrative_generator: Optional narrative generator
        prompt_template: Prompt template for LLM sections
        max_parallel_sections: Maximum parallel LLM calls
        max_output_lines: Maximum output lines per failure
        enable_failure_grouping: Whether to group failures
        max_detailed_failures: Maximum failures in detailed payload

    Returns:
        Markdown content

    """
    md_parts = []

    # Header
    title = _SIGNOFF_TITLES.get(facts.source_format, _SIGNOFF_TITLES["pytest"])
    md_parts.append(f"# {title}\n")
    md_parts.append(f"*Generated: {facts.timestamp_iso}*\n")

    # Deterministic: Run Facts
    md_parts.append("## Test Results Overview\n")
    md_parts.append(format_facts_table(facts))

    if facts.source_format == "k6":
        md_parts.append("## Scenario & Load Model\n")
        md_parts.append(format_k6_scenario_load_model_overview(facts))

    # Deterministic: Pass Rate
    pass_rate = facts.metrics.pass_rate
    md_parts.append(f"**Pass Rate:** {pass_rate.formatted}\n")

    # Generate LLM sections in parallel
    generated_sections = _generate_llm_sections(
        facts=facts,
        narrative_generator=narrative_generator,
        section_types=[
            SectionType.RISK_ASSESSMENT,
            SectionType.RECOMMENDATION,
        ],
        prompt_template=prompt_template,
        max_parallel_sections=max_parallel_sections,
        max_output_lines=max_output_lines,
        enable_failure_grouping=enable_failure_grouping,
        max_detailed_failures=max_detailed_failures,
    )

    # LLM: Risk Assessment
    md_parts.append("## Risk Assessment\n")
    md_parts.append(format_generated_section(generated_sections.get(SectionType.RISK_ASSESSMENT)))

    md_parts.append("## Recommendation\n")
    md_parts.append(format_generated_section(generated_sections.get(SectionType.RECOMMENDATION)))

    # Deterministic: Critical Failures (if any)
    if facts.metrics.failures:
        md_parts.append("## Critical Failures\n")
        md_parts.append(format_failures(facts, max_failures=10, max_output_lines=max_output_lines))

    # Footer
    md_parts.append("## Sign-Off\n")
    md_parts.append("**QA Engineer:** _________________\n\n")
    md_parts.append("**Date:** _________________\n\n")
    md_parts.append("**Approved:** ☐ Yes  ☐ No  ☐ Conditional\n")

    # Input artifacts
    md_parts.append(format_artifacts_section(facts))

    return "\n".join(md_parts)


def generate_sections_parallel(  # noqa: PLR0913
    facts: ReportFacts,
    narrative_generator: NarrativeGenerator,
    section_types: list[SectionType],
    prompt_template: PromptTemplate,
    max_parallel_sections: int,
    max_output_lines: int,
    enable_failure_grouping: bool,
    max_detailed_failures: int,
) -> dict[SectionType, str | None]:
    """Generate multiple LLM sections in parallel using ThreadPoolExecutor.

    Args:
        facts: Test run facts for grounding
        narrative_generator: LLM narrative generator
        section_types: List of section types to generate
        prompt_template: Prompt template for sections
        max_parallel_sections: Maximum parallel workers
        max_output_lines: Maximum output lines per failure
        enable_failure_grouping: Whether to group failures
        max_detailed_failures: Maximum failures in detailed payload

    Returns:
        Dictionary mapping section types to generated content (or None if generation failed)

    """
    logger.info(
        "Generating %d LLM sections in parallel (max_workers=%d)",
        len(section_types),
        max_parallel_sections,
    )

    results = {}

    # Convert facts to JSON for prompts
    try:
        facts_json = json.dumps(
            build_llm_facts_payload(
                facts,
                max_output_lines,
                enable_failure_grouping,
                max_detailed_failures,
            ),
            indent=2,
        )
    except (TypeError, ValueError) as e:
        msg = f"Failed to serialize report facts for LLM prompts: {e}"
        logger.exception("Failed to serialize report facts: %s", msg)
        raise PersistenceError(
            msg,
            suggestion="Ensure report facts contain only JSON-serializable values.",
        ) from e

    # Get system prompt (same for all sections)
    system_prompt = prompt_template.get_system_prompt()

    # Use ThreadPoolExecutor for parallel generation
    with ThreadPoolExecutor(max_workers=max_parallel_sections) as executor:
        # Submit all generation tasks with prompts
        future_to_section = {
            executor.submit(
                narrative_generator.generate,
                SectionPrompt(section_type=section_type, system_prompt=system_prompt),
                prompt_template.get_section_prompt(section_type, facts_json=facts_json),
            ): section_type
            for section_type in section_types
        }

        # Collect results as they complete
        for future in as_completed(future_to_section):
            section_type = future_to_section[future]
            try:
                content = future.result()
                results[section_type] = content
                if content:
                    logger.debug(
                        "Section '%s' generated successfully (%d chars)",
                        section_type.value,
                        len(content),
                    )
                else:
                    logger.warning("Section '%s' returned None", section_type.value)
            except Exception:
                logger.exception("Failed to generate section '%s'", section_type.value)
                results[section_type] = None

    logger.info(
        "Parallel generation complete: %d/%d sections generated",
        sum(1 for v in results.values() if v),
        len(section_types),
    )

    return results


def _generate_llm_sections(  # noqa: PLR0913
    *,
    facts: ReportFacts,
    narrative_generator: NarrativeGenerator | None,
    section_types: list[SectionType],
    prompt_template: PromptTemplate,
    max_parallel_sections: int,
    max_output_lines: int,
    enable_failure_grouping: bool,
    max_detailed_failures: int,
) -> dict[SectionType, str | None]:
    """Generate LLM sections if a generator is available."""
    if not narrative_generator:
        return {}

    return generate_sections_parallel(
        facts,
        narrative_generator,
        section_types,
        prompt_template,
        max_parallel_sections,
        max_output_lines,
        enable_failure_grouping,
        max_detailed_failures,
    )
