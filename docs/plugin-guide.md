# Plugin Development Guide

This guide explains how to extend **qa-report-generator** with custom parsers, writers, and hooks.
It builds on the plugin registry system in `src/qa_report_generator/plugins/registry.py` and the
examples in `examples/`.

## Overview

The plugin system supports three extension points:

1. **Parsers** — Add support for new test report formats (e.g., JUnit XML).
2. **Writers** — Generate reports in new formats (e.g., HTML, PDF, JSON).
3. **Hooks** — Run custom logic at lifecycle events (pre-parse, post-write, etc.).

Plugins can be discovered via:

- **Entry points** (recommended for distributable plugins)
- **Module imports** (useful for local plugins and examples)

## Plugin Discovery

At startup, plugins are discovered in two ways:

1. **Entry points** defined in your package config
2. **Module imports** specified via `PLUGIN_MODULES` (JSON list of module paths)

```bash
export PLUGIN_MODULES='[
  "examples.custom_writer.json_writer",
  "examples.hooks.teams_notifier"
]'
```

### Entry Point Groups

Use these entry-point groups in your package configuration:

```toml
[project.entry-points."qa_report_generator.parsers"]
custom-parser = "my_package.parsers:MyParser"

[project.entry-points."qa_report_generator.writers"]
custom-writer = "my_package.writers:MyWriter"

[project.entry-points."qa_report_generator.hooks"]
custom-hook = "my_package.hooks:register"
```

## Custom Parsers

Parsers must implement `ReportParser` and return a `RunMetrics` instance.

```python
from pathlib import Path

from qa_report_generator.application.ports.output import ReportParser
from qa_report_generator.domain.models import RunMetrics
from qa_report_generator.plugins import register_parser


@register_parser("junit")
class JUnitParser(ReportParser):
    """Parse JUnit XML reports into RunMetrics."""

    def parse(self, filepath: Path) -> RunMetrics:
        # Parse the report and build RunMetrics
        return RunMetrics(...)
```

### Best Practices

- Validate the input format and raise `ParseError` on failure.
- Populate `failures` and `test_results` for analytics.
- Keep parsing in the adapter layer; domain models should remain I/O-free.

## Custom Writers

Writers implement `ReportWriter` and return two paths: summary and sign-off.

```python
from pathlib import Path

from qa_report_generator.application.ports.output import NarrativeGenerator, ReportWriter
from qa_report_generator.domain.models import ReportFacts
from qa_report_generator.plugins import register_writer


@register_writer("html")
class HTMLReportWriter(ReportWriter):
    """Generate HTML reports."""

    def save_reports(
        self,
        facts: ReportFacts,
        output_dir: Path,
        narrative_generator: NarrativeGenerator | None = None,
        prompt_template_path: Path | None = None,
    ) -> tuple[Path, Path]:
        # Write HTML reports and return file paths
        return output_dir / "pytest_summary.html", output_dir / "signoff_report.html"
```

### Example

See `examples/custom_writer/json_writer.py` for a full implementation.

## Lifecycle Hooks

Hooks are simple callables that receive a context dictionary.

```python
from qa_report_generator.plugins import register_hook


@register_hook("post_write")
def notify_team(context: dict) -> None:
    summary_path = context.get("summary_path")
    facts = context.get("facts")
    # Send notification or trigger downstream actions
```

### Available Hook Points

- `pre_parse` — before parsing (context: `filepath`)
- `post_parse` — after parsing (context: `filepath`, `metrics`)
- `pre_generate` — before LLM generation (context: `metrics`)
- `post_generate` — after LLM generation (context: `metrics`, `reports`)
- `post_write` — after writing reports (context: `output_dir`, `summary_path`, `signoff_path`, `facts`)

### Example

See `examples/hooks/teams_notifier.py` for a Teams webhook implementation.

## Testing Plugins

1. Register the plugin via decorator or entry point.
2. Ensure your module is imported (via `PLUGIN_MODULES` or entry points).
3. Run the CLI and verify the plugin behavior.

```bash
export PLUGIN_MODULES='["examples.custom_writer.json_writer"]'
python -m qa_report_generator generate --json-report dummy_project/.pytest-report.json --out out/
```

## Troubleshooting

- **Plugin not found**: Confirm module import or entry point registration.
- **Hook not firing**: Ensure correct hook point name and module import.
- **Parser errors**: Validate report format and surface clear `ParseError` messages.
- **Writer errors**: Raise `PersistenceError` with actionable suggestions.
