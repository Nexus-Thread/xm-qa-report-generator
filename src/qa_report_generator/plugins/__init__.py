"""Plugin system for extending report generation functionality.

This module provides a flexible plugin architecture for customizing:

- **Parsers**: Add support for different test report formats
- **Writers**: Output reports in custom formats (markdown, html, json, etc.)
- **Hooks**: Execute custom logic at lifecycle points during report generation

Usage Examples:

    # Register a custom parser
    from qa_report_generator.plugins import register_parser

    @register_parser("junit-xml")
    class JUnitParser(ReportParser):
        def parse(self, filepath: Path) -> RunMetrics:
            ...

    # Register a custom writer
    from qa_report_generator.plugins import register_writer

    @register_writer("html")
    class HTMLWriter(ReportWriter):
        def save_reports(self, facts, output_dir, narrative_generator, prompt_template_path=None):
            ...

    # Register a lifecycle hook
    from qa_report_generator.plugins import register_hook

    @register_hook("post_write")
    def notify_on_completion(context: dict) -> None:
        print(f"Report generated: {context['summary_path']}")
"""

from qa_report_generator.plugins.registry import (
    PLUGIN_ENTRYPOINT_GROUPS,
    HookRegistry,
    ParserRegistry,
    WriterRegistry,
    discover_plugins,
    register_hook,
    register_parser,
    register_writer,
)

__all__ = [
    "PLUGIN_ENTRYPOINT_GROUPS",
    "HookRegistry",
    "ParserRegistry",
    "WriterRegistry",
    "discover_plugins",
    "register_hook",
    "register_parser",
    "register_writer",
]
