# Extension Examples

This directory contains working examples of how to extend the reporting POC with custom functionality.

## Overview

The reporting POC supports three types of extensions:

1. **Custom Parsers** - Parse different test report formats
2. **Custom Writers** - Generate reports in different formats
3. **Hooks** - Add custom behavior at specific lifecycle points
4. **Custom Prompts** - Customize LLM narrative generation

## Quick Start

### Using Custom Prompts

```bash
# Use your own prompt templates
export PROMPT_TEMPLATE_PATH="examples/custom_prompts/creative_prompts.yaml"
python -m qa_report_generator generate --json-report report.json --out out/
```

### Using Custom Writers (Example)

```python
# In your code, register a custom writer
from examples.custom_writer.json_writer import JSONReportWriter

# The writer will be automatically available
```

### Using Hooks (Example)

```python
# In your code, register hooks
from examples.hooks.teams_notifier import notify_teams

# Hook will be called automatically at post_write
```

## Examples Included

### 1. Custom Prompts

- **`custom_prompts/creative_prompts.yaml`** - More creative, detailed narratives
- **`custom_prompts/concise_prompts.yaml`** - Minimal, brief narratives

### 2. Custom Writers

- **`custom_writer/json_writer.py`** - Generate JSON reports

### 3. Hooks

- **`hooks/teams_notifier.py`** - Send Microsoft Teams notifications

## Creating Your Own Extensions

See the main README for extension guidelines and entry-point setup details.

## Testing Examples

```bash
# Test with creative prompts
PROMPT_TEMPLATE_PATH=examples/custom_prompts/creative_prompts.yaml \
  python -m qa_report_generator generate \
  --json-report dummy_project/.pytest-report.json \
  --out out/

# Compare with default prompts
python -m qa_report_generator generate \
  --json-report dummy_project/.pytest-report.json \
  --out out/
```
