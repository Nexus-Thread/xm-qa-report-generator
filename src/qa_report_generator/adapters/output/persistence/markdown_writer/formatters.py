"""Markdown formatting utilities for report sections."""

from qa_report_generator.domain.analytics.models import HealthMetrics
from qa_report_generator.domain.models import Failure, ReportFacts
from qa_report_generator.domain.models.performance import K6LoadStage, K6ScenarioContext
from qa_report_generator.domain.preprocessors import OutputTruncator


def format_quick_stats_card(facts: ReportFacts) -> str:
    """Render a quick stats card with high-level health indicators.

    Args:
        facts: Test run facts

    Returns:
        Formatted stats card as markdown code block

    """
    metrics = facts.metrics
    pass_rate = metrics.pass_rate
    if pass_rate.is_critical:
        health_label = "🚨 CRITICAL"
    elif pass_rate.is_acceptable:
        health_label = "✅ GOOD"
    else:
        health_label = "⚠️ MARGINAL"

    flaky_count = len(facts.health_metrics.flaky_tests) if facts.health_metrics else 0
    critical_failures = _count_critical_failures(metrics.failures)
    duration_str = f"{metrics.duration_seconds:.2f}s" if metrics.duration_seconds is not None else "n/a"
    total = metrics.total
    failed_pct = (metrics.failed / total * 100) if total else 0.0
    skipped_pct = (metrics.skipped / total * 100) if total else 0.0

    lines = [
        "```",
        "┌─────────────────────────────────────┐",
        f"│  🎯 Test Run Health: {health_label:<14} │",
        "├─────────────────────────────────────┤",
        f"│  ✅ Passed:   {metrics.passed}/{metrics.total} ({metrics.pass_rate.formatted:<6}) │",
        f"│  ❌ Failed:   {metrics.failed}/{metrics.total} ({failed_pct:.1f}%) │",
        f"│  ⏭️  Skipped:  {metrics.skipped}/{metrics.total} ({skipped_pct:.1f}%) │",
        "├─────────────────────────────────────┤",
        f"│  ⏱️  Duration: {duration_str:<16} │",
        f"│  🔥 Critical Failures: {critical_failures:<6} │",
        f"│  ⚠️  Flaky Tests: {flaky_count:<11} │",
        "└─────────────────────────────────────┘",
        "```\n",
    ]

    return "\n".join(lines)


def format_facts_table(facts: ReportFacts) -> str:
    """Render test run facts as a markdown table.

    Args:
        facts: Test run facts to render

    Returns:
        Formatted markdown table

    """
    m = facts.metrics
    env = facts.environment

    lines = [
        "| Metric | Value |",
        "|--------|-------|",
        f"| **Total Tests** | {m.total} |",
        f"| **Passed** | {m.passed} |",
        f"| **Failed** | {m.failed} |",
        f"| **Skipped** | {m.skipped} |",
        f"| **Errors** | {m.errors} |",
    ]

    if m.duration_seconds is not None:
        duration_str = f"{m.duration_seconds:.2f}s"
        lines.append(f"| **Duration** | {duration_str} |")

    if env.env:
        lines.append(f"| **Environment** | {env.env} |")
    if env.build:
        lines.append(f"| **Build** | {env.build} |")
    if env.commit:
        lines.append(f"| **Commit** | {env.commit} |")
    if env.target_url:
        lines.append(f"| **Target URL** | {env.target_url} |")

    return "\n".join(lines) + "\n"


def format_engineering_summary(facts: ReportFacts) -> str:
    """Render deterministic engineering summary from analytics data.

    Args:
        facts: Test run facts with analytics

    Returns:
        Formatted markdown section

    """
    lines: list[str] = []

    if facts.patterns:
        lines.append("**Detected Patterns:**")
        lines.extend(_format_patterns(facts))
    else:
        lines.append("**Detected Patterns:** None\n")

    if facts.health_metrics:
        metrics = facts.health_metrics
        avg_duration = f"{metrics.average_duration_seconds:.2f}s" if metrics.average_duration_seconds is not None else "n/a"
        lines.append("\n**Health Metrics:**")
        lines.append(f"- Average failed test duration: {avg_duration}")
        lines.extend(_format_health_metrics(metrics))

    if facts.quality_score:
        lines.append("\n**Quality Score:**")
        lines.append(f"- Score: {facts.quality_score.score}/100")
        for factor, value in facts.quality_score.factors.items():
            lines.append(f"- {factor.replace('_', ' ').title()}: {value}")

    if facts.test_smells:
        lines.append("\n**Test Smells:**")
        lines.extend(_format_test_smells(facts))

    if facts.failure_clusters:
        lines.append("\n**Failure Clusters:**")
        lines.extend(_format_failure_clusters(facts))

    return "\n".join(lines) + "\n"


def format_failures(facts: ReportFacts, max_failures: int, max_output_lines: int) -> str:
    """Render detailed failure information.

    Args:
        facts: Test run facts containing failure data
        max_failures: Maximum number of failures to include
        max_output_lines: Maximum output lines per failure

    Returns:
        Formatted markdown with failure details

    """
    failures = facts.metrics.failures[:max_failures]

    if not failures:
        return "*No failures recorded.*\n"

    lines = []
    for i, failure in enumerate(failures, 1):
        lines.extend(_format_failure_entry(i, failure, max_output_lines))

    total_failures = len(facts.metrics.failures)
    if total_failures > max_failures:
        remaining = total_failures - max_failures
        lines.append(f"\n*...and {remaining} more failures (truncated)*\n")

    return "\n".join(lines)


def format_artifacts_section(facts: ReportFacts) -> str:
    """Render input artifacts section.

    Args:
        facts: Test run facts containing input file paths

    Returns:
        Formatted markdown section

    """
    lines = ["## Input Artifacts\n"]
    lines.extend(f"- `{filepath}`\n" for filepath in facts.input_files)
    return "".join(lines)


def format_generated_section(content: str | None) -> str:
    """Format generated section content with fallback message.

    Args:
        content: Generated content or None if unavailable

    Returns:
        Formatted section content

    """
    if content:
        return f"{content}\n"
    return "*[LLM unavailable - narrative section skipped]*\n"


def format_k6_scenario_load_model_overview(facts: ReportFacts) -> str:
    """Render a scenario and load-model overview table for k6 reports."""
    k6_context = facts.k6_context
    if not k6_context or not k6_context.scenario_load_models:
        return "*No k6 scenario load-model data available.*\n"

    lines = [
        "| Scenario | Executor | Rate (rps) | Time Unit | Duration | VUs (start/pre/max) | Stages | Checks (pass/fail/total) | Thresholds (pass/fail/total) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]

    for scenario_name in sorted(k6_context.scenario_load_models):
        load_model = k6_context.scenario_load_models[scenario_name]
        scenario_totals = k6_context.by_scenario.get(scenario_name)
        checks_summary = _format_scenario_check_totals(scenario_totals)
        thresholds_summary = _format_scenario_threshold_totals(scenario_totals)
        lines.append(
            "| "
            + " | ".join(
                [
                    scenario_name,
                    load_model.executor,
                    _format_optional_int(load_model.rate),
                    _format_optional_text(load_model.time_unit),
                    _format_optional_text(load_model.duration),
                    _format_vus_triplet(
                        load_model.start_vus,
                        load_model.pre_allocated_vus,
                        load_model.max_vus,
                    ),
                    _format_stages(load_model.stages),
                    checks_summary,
                    thresholds_summary,
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def _format_failure_entry(index: int, failure: Failure, max_output_lines: int) -> list[str]:
    """Format a single failure entry.

    Args:
        index: Failure number in the list
        failure: Failure to format
        max_output_lines: Maximum output lines to include

    Returns:
        List of formatted markdown lines

    """
    lines = [f"### {index}. `{failure.test_name}`\n", f"**Suite:** `{failure.suite}`\n"]

    if failure.type:
        lines.append(f"**Type:** `{failure.type}`\n")
    if failure.duration:
        lines.append(f"**Duration:** `{failure.duration.formatted}`\n")

    if failure.output:
        lines.extend(_format_failure_output(failure, max_output_lines))

    lines.extend(_format_failure_message(failure.message))

    return lines


def _format_failure_output(failure: Failure, max_output_lines: int) -> list[str]:
    """Format captured output for a failure.

    Args:
        failure: Failure with output
        max_output_lines: Maximum lines to include

    Returns:
        List of formatted markdown lines

    """
    lines: list[str] = []
    output = OutputTruncator(
        max_head_lines=max_output_lines,
        max_tail_lines=0,
    ).truncate_output(failure.output)
    if not output:
        return lines

    if output.stdout:
        lines.append("\n**Captured stdout:**\n```\n")
        lines.append(output.stdout)
        lines.append("\n```\n")

    if output.stderr:
        lines.append("\n**Captured stderr:**\n```\n")
        lines.append(output.stderr)
        lines.append("\n```\n")

    if output.log:
        lines.append("\n**Captured log:**\n```\n")
        lines.append(output.log)
        lines.append("\n```\n")

    return lines


def _format_failure_message(message: str) -> list[str]:
    """Format failure message with truncation.

    Args:
        message: Failure message

    Returns:
        List of formatted markdown lines

    """
    max_message_length = 500
    if len(message) > max_message_length:
        message = message[:max_message_length] + "... (truncated)"

    return [
        "\n**Failure Details:**\n```\n",
        message,
        "\n```\n",
    ]


def _format_patterns(facts: ReportFacts) -> list[str]:
    """Format detected patterns list."""
    return [f"- ({pattern.severity}) {pattern.description} (tests: {len(pattern.affected_tests)})" for pattern in facts.patterns]


def _format_health_metrics(metrics: HealthMetrics) -> list[str]:
    """Format health metrics details."""
    lines = []
    if metrics.slowest_tests:
        slowest = ", ".join(f"{timing.test_name} ({timing.duration_seconds:.2f}s)" for timing in metrics.slowest_tests)
        lines.append(f"- Slowest failures: {slowest}")
    if metrics.flaky_tests:
        lines.append(f"- ⚠️ Potentially flaky tests: {', '.join(metrics.flaky_tests)}")
    return lines


def _format_test_smells(facts: ReportFacts) -> list[str]:
    """Format test smells list."""
    return [f"- ({smell.severity}) {smell.description} (tests: {len(smell.affected_tests)})" for smell in facts.test_smells]


def _format_failure_clusters(facts: ReportFacts) -> list[str]:
    """Format failure cluster summaries."""
    return [f"- {cluster.count}x {cluster.representative.type or 'UnknownError'}: {cluster.representative.message}" for cluster in facts.failure_clusters]


def _count_critical_failures(failures: list[Failure]) -> int:
    """Count critical failures by type.

    Args:
        failures: List of failures to analyze

    Returns:
        Count of critical failures

    """
    critical_types = {"systemerror", "memoryerror", "keyerror"}
    return sum(1 for failure in failures if (failure.type or "").lower() in critical_types)


def _format_optional_text(value: str | None) -> str:
    """Format optional text values with fallback."""
    if value is None or not value:
        return "N/A"
    return value


def _format_optional_int(value: int | None) -> str:
    """Format optional integer values with fallback."""
    if value is None:
        return "N/A"
    return str(value)


def _format_vus_triplet(start_vus: int | None, pre_allocated_vus: int | None, max_vus: int | None) -> str:
    """Format start/pre/max VU values as a compact triplet."""
    return "/".join(
        [
            _format_optional_int(start_vus),
            _format_optional_int(pre_allocated_vus),
            _format_optional_int(max_vus),
        ]
    )


def _format_stages(stages: list[K6LoadStage]) -> str:
    """Format stage list as duration→target sequence."""
    if not stages:
        return "N/A"
    return ", ".join(f"{stage.duration}→{stage.target}" for stage in stages)


def _format_scenario_check_totals(scenario_totals: K6ScenarioContext | None) -> str:
    """Format scenario check totals summary."""
    if scenario_totals is None:
        return "N/A"
    return f"{scenario_totals.checks_passed}/{scenario_totals.checks_failed}/{scenario_totals.checks_total}"


def _format_scenario_threshold_totals(scenario_totals: K6ScenarioContext | None) -> str:
    """Format scenario threshold totals summary."""
    if scenario_totals is None:
        return "N/A"
    return f"{scenario_totals.thresholds_passed}/{scenario_totals.thresholds_failed}/{scenario_totals.thresholds_total}"
