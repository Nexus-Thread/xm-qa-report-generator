"""Built-in parser plugins.

This package contains parser plugins that implement the ReportParser interface
to parse different test report formats (e.g., pytest-json, junit-xml).

Custom parsers can be added here and registered using the @register_parser decorator:

    from qa_report_generator.plugins import register_parser

    @register_parser("custom-format")
    class CustomParser(ReportParser):
        def parse(self, filepath: Path) -> RunMetrics:
            # Parse your custom format
            ...

Or register them programmatically using ParserRegistry.register().
"""
