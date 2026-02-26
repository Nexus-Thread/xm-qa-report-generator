"""Composition root for the k6-only CLI."""

from qa_report_generator.adapters.input.cli_adapter import K6CliAdapter
from qa_report_generator.adapters.input.env import EnvSettingsAdapter
from qa_report_generator.adapters.output.parsers import K6SummaryTableParser
from qa_report_generator.adapters.output.persistence.performance import K6SummaryTableMarkdownWriter
from qa_report_generator.application.use_cases import K6SummaryTableService
from qa_report_generator.config import setup_logging
from qa_report_generator.plugins import discover_plugins


def create_cli_adapter() -> K6CliAdapter:
    """Create a k6-only CLI adapter with dependencies wired."""
    config = EnvSettingsAdapter().load()

    setup_logging(config)
    discover_plugins(config.plugin_modules)

    k6_summary_table_use_case = K6SummaryTableService(
        parser=K6SummaryTableParser(),
        writer=K6SummaryTableMarkdownWriter(),
    )
    return K6CliAdapter(generate_k6_summary_table_use_case=k6_summary_table_use_case)


def main() -> None:
    """Run the k6-only CLI application."""
    cli = create_cli_adapter()
    cli.run()


if __name__ == "__main__":
    main()
