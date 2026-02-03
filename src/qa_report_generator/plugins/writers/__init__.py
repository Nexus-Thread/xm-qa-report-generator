"""Built-in writer plugins.

This package contains writer plugins that implement the ReportWriter interface
to output reports in different formats (e.g., markdown, html, json).

Custom writers can be added here and registered using the @register_writer decorator:

    from qa_report_generator.plugins import register_writer

    @register_writer("custom-format")
    class CustomWriter(ReportWriter):
        def save_reports(self, facts, output_dir, narrative_generator, prompt_template_path=None):
            # Generate and save reports in your custom format
            ...

Or register them programmatically using WriterRegistry.register().
"""
