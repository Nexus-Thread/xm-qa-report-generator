# QA Report Generator

Demonstrate LLM value beyond code generation: intelligent reporting from pytest results using Ollama's local LLM.

> **Status:** Proof of Concept. This project is not production-ready. Treat the guidance below as exploratory and validate in staging before any production adoption.

## Overview

This tool generates two professional markdown reports from pytest JSON reports:

1. **Pytest Summary Report** (`out/pytest_summary.md`) - Technical test run overview with LLM-generated executive summary and key observations
2. **QA Sign-Off Report** (`out/signoff_report.md`) - Management-focused report with risk assessment and go/no-go recommendation

### Key Features

- ✅ **Deterministic metrics extraction** - Numbers are always correct, even if LLM fails
- 🤖 **LLM-enhanced narratives** - Executive summaries, risk assessments, and recommendations
- 🔒 **Grounded generation** - LLM forbidden from inventing numbers or failures
- 🛡️ **Graceful degradation** - Reports still generate when LLM is unavailable
- 🏠 **Local-first** - Uses Ollama (local) instead of OpenAI cloud

## Prerequisites

### Required

- Python 3.11 or higher
- [Ollama](https://ollama.ai/) installed and running locally

### Install Ollama (if not already installed)

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or via Homebrew (macOS)
brew install ollama

# Start Ollama service
ollama serve
```

### Pull a model

```bash
# Download llama3.2 (default model)
ollama pull llama3.2

# Or use another model like mistral
ollama pull mistral
```

## Installation

1. **Clone the repository**

```bash
cd /Users/ondra/Documents/Projects/xm.nosync/qa-report-generator
```

2. **Create a virtual environment**

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install the package**

```bash
pip install -e .
```

For development (includes pytest):

```bash
pip install -e ".[dev]"
```

## Configuration

Configure via environment variables or `.env` file using a single OpenAI-compatible endpoint:

### OpenAI-Compatible (Cloud or Local)

```bash
# Core LLM settings
export LLM_MODEL="gpt-5.2"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-..."  # or "not-needed" for local services

# Optional generation settings
export LLM_TEMPERATURE="0.0" # not valid for reasoning models
export LLM_REASONING_EFFORT="high"  # only for reasoning models
export LLM_TIMEOUT="100.0"
export LLM_MAX_RETRIES="3"
export LLM_RETRY_BACKOFF_FACTOR="2.0"
```

### Examples

```bash
# OpenAI cloud
export LLM_MODEL="gpt-5.2"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_API_KEY="sk-..."

# Ollama local (OpenAI-compatible)
export LLM_MODEL="llama3.2:1b-instruct-q5_K_M"
export LLM_BASE_URL="http://localhost:11434/v1"
export LLM_API_KEY="not-needed"
```

### Additional Settings

```bash
# Performance: Parallel LLM section generation
export MAX_PARALLEL_LLM_SECTIONS="1"  # 1-10

# Prompt optimization
export MAX_OUTPUT_LINES_PER_FAILURE="20"  # 1-200
export ENABLE_FAILURE_GROUPING="true"  # true/false
export FAILURE_CLUSTERING_THRESHOLD="0.7"  # 0.0-1.0
export MAX_FAILURES_FOR_DETAILED_PROMPT="10"  # 1-200

# Logging
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
export LOG_FORMAT="simple"  # simple or json
```

### Configuration Options

| Variable                           | Description                                      | Default                     | Valid Range                           |
| ---------------------------------- | ------------------------------------------------ | --------------------------- | ------------------------------------- |
| `LLM_MODEL`                        | LLM model name                                   | `gpt-5.2`                   | Any OpenAI-compatible model           |
| `LLM_BASE_URL`                     | LLM API endpoint                                 | `https://api.openai.com/v1` | Any valid URL                         |
| `LLM_API_KEY`                      | API key                                          | `not-needed`                | Any string                            |
| `LLM_TEMPERATURE`                  | Sampling temperature                             | None (provider default)     | 0.0 - 2.0                             |
| `LLM_REASONING_EFFORT`             | Reasoning effort (if supported)                  | None                        | low/medium/high                       |
| `LLM_TIMEOUT`                      | API request timeout in seconds                   | `100.0`                     | Any positive number                   |
| `LLM_MAX_RETRIES`                  | Maximum retry attempts                           | `3`                         | 0 - 10                                |
| `LLM_RETRY_BACKOFF_FACTOR`         | Exponential backoff multiplier                   | `2.0`                       | 1.0 - 10.0                            |
| `MAX_PARALLEL_LLM_SECTIONS`        | Parallel section generation                      | `1`                         | 1 - 10                                |
| `MAX_OUTPUT_LINES_PER_FAILURE`     | Max output lines per failure in LLM payloads     | `20`                        | 1 - 200                               |
| `ENABLE_FAILURE_GROUPING`          | Group failures by signature before prompting     | `true`                      | true/false                            |
| `FAILURE_CLUSTERING_THRESHOLD`     | Similarity threshold for failure clustering      | `0.7`                       | 0.0 - 1.0                             |
| `MAX_FAILURES_FOR_DETAILED_PROMPT` | Cap for detailed failure payloads                | `10`                        | 1 - 200                               |
| `LOG_LEVEL`                        | Logging verbosity                                | `INFO`                      | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `LOG_FORMAT`                       | Logging output format                            | `simple`                    | simple, json                          |
| `PLUGIN_MODULES`                   | JSON list of plugin modules to import at startup | `[]`                        | JSON array of module paths            |

## Usage

### Quick Start

```bash
# Generate reports from pytest JSON report
python -m qa_report_generator generate --json-report tests/fixtures/pytest_report_sample.json --out out/
```

### Full Example with Environment Metadata

```bash
python -m qa_report_generator generate \
  --json-report path/to/report.json \
  --out out/ \
  --env staging \
  --build 456 \
  --commit abc123def \
  --target-url https://staging.example.com
```

### Disable LLM (Deterministic Only)

```bash
python -m qa_report_generator generate \
  --json-report tests/fixtures/pytest_report_sample.json \
  --out out/ \
  --no-llm
```

### Validate Configuration

Before generating reports, you can validate your configuration:

```bash
# Validate configuration
python -m qa_report_generator validate-config

# Or use the installed command
qa-report-generator validate-config
```

This command will:

- ✅ Validate all configuration settings
- ✅ Display configuration warnings if any

**Example output:**

```
🔍 Validating configuration...

📋 Configuration:
  Base URL: http://localhost:11434/v1
  Model: llama3.2:1b-instruct-q5_K_M
  Temperature: 0.0
  Timeout: 100.0s
  Log Level: INFO
  Log Format: simple

✅ Configuration is valid.
```

This is especially useful for:

- 🔧 Debugging configuration issues
- 🚀 Verifying setup in CI/CD pipelines
- 🏥 Health checks before report generation

### Generate Reports Options

| Option                    | Description                                                | Default |
| ------------------------- | ---------------------------------------------------------- | ------- |
| `--json-report`           | Path to pytest-json-report JSON file (required)            | -       |
| `--out`                   | Output directory for reports                               | `out/`  |
| `--env`                   | Environment name (e.g., staging, production)               | None    |
| `--build`                 | Build number or ID                                         | None    |
| `--commit`                | Git commit hash                                            | None    |
| `--target-url`            | Target application URL                                     | None    |
| `--max-failures`          | Maximum failures to include (use -1 to disable limiting)   | 20      |
| `--no-llm`                | Disable LLM narrative generation                           | False   |
| `--regenerate-narratives` | Reuse cached parsed metrics and regenerate LLM narratives  | False   |
| `--verbose`, `-v`         | Enable verbose output with detailed progress               | False   |
| `--quiet`, `-q`           | Minimal output (only results and errors)                   | False   |
| `--dry-run`               | Validate inputs without generating reports                 | False   |
| `diff` command            | Compare two pytest JSON reports and show regressions       | -       |
| `--profile`               | Preprocessing profile preset (minimal, balanced, detailed) | None    |

### CLI Output Modes

The CLI supports three verbosity levels for different use cases:

**Normal Mode (default)**

```bash
python -m qa_report_generator generate --json-report report.json --out out/
```

Shows:

- Progress indicators with spinner and progress bar
- Status messages for each step
- Success messages with file paths and sizes
- Color-coded output (🟢 green for success, 🔵 blue for info, 🔴 red for errors)

**Verbose Mode** (`--verbose` or `-v`)

```bash
python -m qa_report_generator generate --json-report report.json --out out/ --verbose
```

Shows everything from normal mode plus:

- Detailed timing information for each step
- File paths and sizes for inputs
- LLM status and model information
- Summary table with all generated reports
- Total generation time

**Quiet Mode** (`--quiet` or `-q`)

```bash
python -m qa_report_generator generate --json-report report.json --out out/ --quiet
```

Shows only:

- Final output file paths
- Errors (if any occur)

Perfect for CI/CD pipelines or when you just want the results.

**Dry-Run Mode** (`--dry-run`)

```bash
python -m qa_report_generator generate --json-report report.json --out out/ --dry-run
```

Validates everything without generating reports:

- ✅ Checks input file exists and is readable
- ✅ Parses JSON structure to ensure validity
- ✅ Verifies output directory is writable
- ✅ Shows what would be generated

Great for:

- Pre-flight checks before actual generation
- CI/CD validation stages
- Troubleshooting configuration issues

**Examples:**

```bash
# Quick validation before generating
python -m qa_report_generator generate --json-report report.json --dry-run

# Verbose output for debugging
python -m qa_report_generator generate \
  --json-report report.json \
  --out out/ \
  --env staging \
  --verbose

# Quiet mode for scripting
python -m qa_report_generator generate --json-report report.json --out out/ --quiet
if [ $? -eq 0 ]; then
  echo "Success"
fi

# Combine flags (verbose dry-run for maximum information)
python -m qa_report_generator generate --json-report report.json --dry-run --verbose
```

### Preprocessing Profiles

Use `--profile` or the `PREPROCESSING_PROFILE` env var to apply preset preprocessing defaults.

```bash
python -m qa_report_generator generate --json-report report.json --profile minimal
```

## Generating Test Artifacts

This tool requires pytest JSON reports generated using the `pytest-json-report` plugin.

**Why JSON report?** It captures everything: stdout, stderr, logs, per-test durations, and full stack traces. Perfect for debugging and giving LLM rich context.

### Installation

```bash
# Install pytest-json-report plugin
pip install pytest-json-report
```

### Running Tests

```bash
# Run tests with JSON report
pytest --json-report --json-report-file=out/report.json
```

### Generating Reports

```bash
# Generate enhanced reports with captured outputs
python -m qa_report_generator generate \
  --json-report out/report.json \
  --out out/ \
  --env staging \
  --build 123
```

### What You Get

The pytest JSON report format provides rich context:

- ✅ Captured stdout/stderr from each test
- ✅ Captured log messages
- ✅ Per-test duration
- ✅ Setup/teardown/call phase outputs separately
- ✅ Full environment info (Python version, packages, etc.)

**Example output enhancement:**

Instead of just seeing "AssertionError: Expected 401, got 200", you'll see:

```markdown
**Captured stdout:**
```

DEBUG: Attempting login with user=test@example.com
INFO: Making POST request to /api/login
ERROR: Authentication check bypassed

```

**Failure Details:**
```

AssertionError: Expected 401, got 200

```

```

This makes debugging failures much easier and provides the LLM with actual context!

### Recommended Workflow

```bash
# 1. Validate configuration (optional but recommended)
python -m qa_report_generator validate-config

# 2. Run your tests and generate JSON report
pytest tests/ \
  --json-report \
  --json-report-file=out/report.json

# 3. Generate rich reports
python -m qa_report_generator generate \
  --json-report out/report.json \
  --out out/ \
  --env staging \
  --build $(git rev-parse --short HEAD) \
  --commit $(git rev-parse HEAD)

# 4. View reports
open out/pytest_summary.md
open out/signoff_report.md
```

## Testing with dummy_project

The repository includes a `dummy_project/` directory with a comprehensive test suite designed to generate realistic pytest reports for testing this reporting POC.

### Quick Start

```bash
# Install dev dependencies (from root project)
uv sync --all-extras

# Run dummy_project tests
cd dummy_project
pytest

# This creates .pytest-report.json with ~110-120 tests
# Including: passing, failing, errors, skipped, and tests with output
```

### Generate Reports from dummy_project

```bash
# From project root
cd ..

# Generate comprehensive reports
qa-report-generator generate \
    --json-report dummy_project/.pytest-report.json \
    --out reports/ \
    --env staging \
    --build 123
```

### What's Included

The dummy_project contains intentionally designed test scenarios:

- ✅ **~50 passing tests** - Various successful scenarios
- ❌ **~30 failing tests** - Assertion errors with different types
- 🔥 **~15 error tests** - Runtime exceptions (ValueError, TypeError, etc.)
- ⏭️ **~10 skipped tests** - Various skip conditions
- 📝 **~10 tests with output** - stdout/stderr/logging capture
- 🔢 **~35 parametrized tests** - Mixed pass/fail scenarios
- ⏱️ **~15 tests with varying durations** - Fast to slow (0.01s to 2s)

See `dummy_project/README.md` for detailed documentation.

## Extensibility

The reporting POC is designed to be highly extensible. You can customize and extend it in several ways:

For a complete guide, see [docs/plugin-guide.md](docs/plugin-guide.md).

### 1. Custom Prompt Templates

Customize how the LLM generates narratives by providing your own prompt templates:

```bash
# Use custom prompts
export PROMPT_TEMPLATE_PATH="my_custom_prompts.yaml"
python -m qa_report_generator generate --json-report report.json --out out/

# Try the included examples
export PROMPT_TEMPLATE_PATH="examples/custom_prompts/creative_prompts.yaml"
python -m qa_report_generator generate --json-report report.json --out out/
```

**Prompt Template Format (YAML):**

```yaml
system_prompt: |
  Instructions for the LLM's behavior and constraints

sections:
  executive_summary:
    prompt: |
      Generate executive summary using {facts_json}

  key_observations:
    prompt: |
      Generate key observations using {facts_json}
```

**Included Examples:**

- `examples/custom_prompts/creative_prompts.yaml` - Detailed, expressive narratives
- `examples/custom_prompts/concise_prompts.yaml` - Brief, minimal narratives

**Adaptive prompt templates (built-in):**

- `src/qa_report_generator/templates/prompts_detailed.yaml` - Used for small test runs (<= 50 tests)
- `src/qa_report_generator/templates/prompts.yaml` - Balanced default for medium runs
- `src/qa_report_generator/templates/prompts_summary.yaml` - Used for large test runs (>= 200 tests)

### 2. Custom Writers

Create custom report writers to generate reports in different formats (HTML, PDF, JSON, etc.):

```python
from qa_report_generator.plugins import register_writer
from qa_report_generator.application.ports.output import ReportWriter

@register_writer("html")
class HTMLReportWriter(ReportWriter):
    def save_reports(self, facts, output_dir, narrative_generator=None, prompt_template_path=None):
        # Generate HTML reports
        pass
```

**Example:** See `examples/custom_writer/json_writer.py` for a complete JSON writer implementation.

#### Plugin Discovery

Plugins are discovered at startup in two ways:

1. **Entry points** (recommended for distributable plugins)
2. **Module imports** (useful for local or example plugins)

To import plugin modules at startup, set `PLUGIN_MODULES` as a JSON list:

```bash
export PLUGIN_MODULES='["examples.custom_writer.json_writer", "examples.hooks.teams_notifier"]'
```

For entry points, register plugins in your package configuration using these groups:

```toml
[project.entry-points."qa_report_generator.parsers"]
custom-parser = "my_package.parsers:MyParser"

[project.entry-points."qa_report_generator.writers"]
custom-writer = "my_package.writers:MyWriter"

[project.entry-points."qa_report_generator.hooks"]
custom-hook = "my_package.hooks:register"
```

### 3. Lifecycle Hooks

Add custom behavior at specific points during report generation:

```python
from qa_report_generator.plugins import register_hook

@register_hook("post_write")
def notify_team(context):
    """Send notification after reports are generated."""
    summary_path = context["summary_path"]
    facts = context["facts"]
    # Send notification (Slack, email, etc.)
    pass
```

**Hook Points:**

- `pre_parse` - Before parsing input file
- `post_parse` - After parsing, before processing
- `pre_generate` - Before LLM generation
- `post_generate` - After LLM generation
- `post_write` - After reports written

**Example:** See `examples/hooks/teams_notifier.py` for a Microsoft Teams notification hook.

### 4. Custom Parsers

Parse different test report formats (JUnit XML, TAP, custom formats):

```python
from qa_report_generator.plugins import register_parser
from qa_report_generator.application.ports.output import ReportParser

@register_parser("junit")
class JUnitParser(ReportParser):
    def parse(self, filepath):
        # Parse JUnit XML format
        return RunMetrics(...)
```

### Learn More

See the examples directory and the extension sections below for details on custom parsers, writers, and hooks.

## Development

### Run Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=src/qa_report_generator --cov-report=html

# Run specific test file
pytest tests/test_junit_parser.py -v
```

### Project Structure

```
qa-report-generator/
├── src/
│   └── qa_report_generator/
│       ├── cli.py                                 # CLI entrypoint
│       ├── config.py                              # App configuration
│       ├── adapters/
│       │   ├── input/cli_adapter/                 # CLI adapter
│       │   │   ├── adapter.py
│       │   │   ├── commands.py
│       │   │   └── ...
│       │   └── output/
│       │       ├── narrative/llm_adapter/         # LLM adapter
│       │       │   ├── adapter.py
│       │       │   └── ...
│       │       ├── parsers/pytest_json_parser/    # Pytest parser
│       │       │   ├── parser.py
│       │       │   └── ...
│       │       └── persistence/markdown_writer/   # Markdown reports
│       │           ├── adapter.py
│       │           ├── formatters.py
│       │           └── ...
│       ├── application/                           # Use cases and ports
│       ├── domain/                                # Domain models and value objects
│       ├── plugins/                               # Plugin registry
│       └── templates/                             # Prompt templates
├── tests/
│   ├── unit/
│   └── int/
└── pyproject.toml                                 # Package configuration
```

## Architecture

### Design Principles

1. **Facts-First Approach**: Extract all metrics deterministically, then pass to LLM as grounding
2. **Never Invent**: LLM explicitly instructed to use only provided facts
3. **Graceful Degradation**: Reports work without LLM, just skip narrative sections
4. **Type Safety**: Pydantic models throughout for validation
5. **Prompt Optimization**: Failures are grouped and outputs are truncated before LLM prompting

### Data Flow

```
Pytest JSON → Parser → RunMetrics → ReportFacts (JSON) → LLM → Markdown Reports
                            ↓
                    Deterministic sections (always present)
```

### LLM Integration

- Uses an OpenAI-compatible API endpoint
- System prompt enforces strict grounding rules
- Use a low temperature (e.g., 0.3) for factual consistency
- Connection errors handled gracefully

## Examples

### Sample Output Structure

**pytest_summary.md:**

- Run Facts (deterministic table)
- Executive Summary (LLM-generated)
- Key Observations (LLM-generated)
- Top Failures (deterministic list)
- Input Artifacts

**signoff_report.md:**

- Test Results Overview (deterministic table)
- Pass Rate calculation
- Risk Assessment (LLM-generated)
- Recommendation (LLM-generated)
- Critical Failures (deterministic)
- Sign-off section with checkboxes

### Try with Sample Data

```bash
# Use included sample fixture
python -m qa_report_generator generate \
  --json-report tests/fixtures/pytest_report_sample.json \
  --out out/ \
  --env staging \
  --build 123

# View results
cat out/pytest_summary.md
cat out/signoff_report.md
```

## Logging

The application includes comprehensive logging to help with debugging and monitoring. By default, logs are written to stderr at the INFO level.

### Log Levels

Control logging verbosity with the `LOG_LEVEL` environment variable:

```bash
# DEBUG: Detailed information for diagnosing problems
export LOG_LEVEL=DEBUG
python -m qa_report_generator generate --json-report report.json --out out/

# INFO: Confirmation that things are working as expected (default)
export LOG_LEVEL=INFO

# WARNING: Something unexpected happened, but the application is still working
export LOG_LEVEL=WARNING

# ERROR: A serious problem prevented a function from working
export LOG_LEVEL=ERROR
```

### Log Formats

Choose between human-readable and machine-parseable formats:

**Simple Format (default):**

```
2026-01-25 20:55:00 - qa_report_generator.adapters.output.parsers.pytest_json_parser - INFO - Starting parse of pytest JSON report: report.json
```

**JSON Format (for log aggregation):**

```bash
export LOG_FORMAT=json
python -m qa_report_generator generate --json-report report.json --out out/
```

Output:

```json
{
  "timestamp": "2026-01-25T20:55:00",
  "level": "INFO",
  "module": "pytest_json_parser",
  "function": "parse",
  "message": "Starting parse of pytest JSON report: report.json"
}
```

### What Gets Logged

- **Parser** (`pytest_json_parser`):
  - Parse start/completion with file paths and test counts
  - File size for debugging
  - Parse errors with line/column numbers for JSON issues

- **Use Case** (`use_cases`):
  - Workflow start/completion with timing
  - Each major step (parsing, limiting, generation)
  - LLM enabled/disabled status
  - Performance metrics

- **Report Writer** (`markdown_writer`):
  - Directory creation
  - File write operations with paths and sizes
  - Report generation success/failure

- **LLM Adapter** (`llm_adapter`):
  - LLM generation attempts and failures
  - Prompt token usage estimates (DEBUG)
  - Graceful degradation warnings

### Example: Debug Mode

```bash
# Enable detailed logging for troubleshooting
LOG_LEVEL=DEBUG python -m qa_report_generator generate \
  --json-report tests/fixtures/pytest_report_sample.json \
  --out out/

# Output will include:
# - File sizes
# - Test counts
# - Timing information for each step
# - Detailed error context
```

## Troubleshooting

### Common Error Codes

The application uses structured error codes to help diagnose issues quickly:

#### Parse Errors

**ERR_PARSE_FILE_NOT_FOUND**

```
Report file not found: path/to/report.json
💡 Suggestion: Check the file path and ensure pytest-json-report plugin generated the report.
```

**Solution:**

- Verify the file path is correct
- Run pytest with `--json-report` flag to generate the report
- Check that pytest-json-report plugin is installed: `pip install pytest-json-report`

**ERR_PARSE_INVALID_JSON**

```
Invalid JSON in report file: report.json (line 42, column 15)
💡 Suggestion: The JSON file is malformed at line 42. Ensure pytest-json-report completed successfully.
```

**Solution:**

- Check if pytest crashed during test run (file may be truncated)
- Re-run pytest to generate a fresh report
- Verify disk space was available during test run

**ERR_PARSE_INVALID_FORMAT**

```
Failed to parse report data: missing required field 'summary'
💡 Suggestion: The JSON structure doesn't match pytest-json-report format.
```

**Solution:**

- Ensure you're using pytest-json-report, not other JSON formats
- Update pytest-json-report to latest version: `pip install -U pytest-json-report`
- Check the JSON file was generated by pytest-json-report plugin

#### Configuration Errors

**ERR_CONFIG_INVALID_URL**

```
Base URL must start with http:// or https://, got: localhost:11434
💡 Suggestion: Check the URL format in your .env file (e.g., http://localhost:11434/v1)
```

**Solution:**

- Update configuration in `.env`:
  - Set `LLM_BASE_URL` to your OpenAI-compatible endpoint
  - For OpenAI: `LLM_BASE_URL=https://api.openai.com/v1`
  - For Azure OpenAI: `LLM_BASE_URL=https://YOUR-RESOURCE.openai.azure.com/`

#### LLM Errors

**ERR_LLM_CONNECTION**

```
Cannot connect to LLM service at http://localhost:11434/v1
💡 Suggestion: Check that the LLM service is running. For Ollama: run 'ollama serve'.
```

**Solution:**

1. **Check Ollama is running:**

   ```bash
   # Start Ollama service
   ollama serve

   # Or check if it's already running
   curl http://localhost:11434/api/tags
   ```

2. **Verify the endpoint:**

   ```bash
   # Should return list of models
   curl http://localhost:11434/v1/models
   ```

3. **Check firewall/network:**
   - Ensure port 11434 is not blocked
   - If using Docker, check port mapping

**ERR_LLM_TIMEOUT**

```
LLM request timed out after waiting for response (model: llama3.2)
💡 Suggestion: Increase LLM_TIMEOUT in .env or try a faster model. Current timeout: 100.0s
```

**Solution:**

- Increase timeout in `.env`: `LLM_TIMEOUT=200.0`
- Use a smaller/faster model:
  ```bash
  ollama pull llama3.2:1b    # Faster but less capable
  ```
- Check system resources (CPU/RAM) - model may be struggling

**ERR_LLM_INIT**

```
Failed to initialize LLM client: Authentication failed
💡 Suggestion: Check your LLM_API_KEY in .env file. For local services like Ollama, use 'not-needed'.
```

**Solution:**

- For local: Set `LLM_API_KEY=not-needed` in `.env`
- For OpenAI: Get API key from https://platform.openai.com/api-keys
- For Azure OpenAI: Use your Azure API key

### LLM Connection Issues

If you see `Warning: LLM generation failed`, the application will gracefully degrade and generate reports without LLM-enhanced sections.

**Quick Checklist:**

1. **Ollama is running:**

   ```bash
   # Check Ollama status
   ollama list

   # Should show your models
   ```

2. **Model is pulled:**

   ```bash
   # Pull the default model
   ollama pull llama3.2:1b-instruct-q5_K_M

   # Or use a different model
   ollama pull mistral
   ```

3. **Correct configuration:**
   ```bash
   # Check .env file
   cat .env | grep LLM_BASE_URL
   ```

# Example: LLM_BASE_URL=http://localhost:11434/v1

````

4. **Service is accessible:**
```bash
# Test the endpoint
curl http://localhost:11434/api/tags

# Should return JSON with models list
````

Reports will still generate with deterministic sections and a note that LLM is unavailable.

### Debug Mode

Enable detailed logging to diagnose issues:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m qa_report_generator generate \
  --json-report report.json \
  --out out/

# You'll see:
# - File sizes and paths
# - Parsing details with line numbers
# - LLM request/response logging
# - Timing information for each step
```

### Validation Errors

If you see Pydantic validation errors:

```bash
# Example: Invalid temperature
ValidationError: 1 validation error for Config
openai_temperature
  Input should be less than or equal to 2.0
```

**Solution:**

- Check `.env` file for typos
- Ensure values are in valid ranges (see Configuration Options table)
- Remove invalid environment variables and restart

### Import Errors

If you see import errors:

```bash
# Reinstall package in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Test Failures

```bash
# Run tests with verbose output
pytest -v

# Check specific test
pytest tests/test_junit_parser.py::test_parse_junit_sample -v
```

## Extending

### Add New Input Format

1. Create a parser implementing `ReportParser` (e.g., in `src/qa_report_generator/adapters/output/parsers/` or a plugin module)
2. Return a `RunMetrics` object
3. Register it via `register_parser` or package entry points

### Customize LLM Prompts

Edit prompts in `src/qa_report_generator/templates/prompts.yaml`, or point `PROMPT_TEMPLATE_PATH` to a custom YAML file.
For built-in adaptive templates, adjust `prompts_detailed.yaml` or `prompts_summary.yaml` as needed.

### Add New Report Sections

Edit `src/qa_report_generator/adapters/output/persistence/markdown_writer.py` and update `src/qa_report_generator/templates/prompts.yaml`:

- Add new sections in `_render_pytest_summary()` or `_render_signoff_report()`
- Keep deterministic sections separate from LLM-generated ones

## FAQ (Frequently Asked Questions)

### General Usage

**Q: When should I use this tool instead of raw pytest output?**

A: Use this tool when you need:

- Executive summaries for non-technical stakeholders
- Risk assessments and go/no-go recommendations for releases
- Management-focused sign-off reports
- AI-enhanced insights about test patterns and issues
- Structured markdown reports for documentation/artifacts

Raw pytest output is great for developers debugging tests. This tool bridges the gap between raw test data and business communication.

**Q: Can I use different LLM providers (OpenAI, Azure, Anthropic, etc.)?**

A: Yes! The tool supports any OpenAI-compatible endpoint via `LLM_BASE_URL`:

- **OpenAI**: Set `LLM_BASE_URL=https://api.openai.com/v1` and `LLM_API_KEY=sk-...`
- **Ollama**: Set `LLM_BASE_URL=http://localhost:11434/v1` and `LLM_API_KEY=not-needed`
- **Azure OpenAI**: Set `LLM_BASE_URL=https://YOUR-RESOURCE.openai.azure.com/`
- **LM Studio**: Use LM Studio's OpenAI-compatible endpoint

**Q: How do I disable LLM features?**

A: Use the `--no-llm` flag:

```bash
python -m qa_report_generator generate --json-report report.json --out out/ --no-llm
```

Reports will still generate with all deterministic metrics, just without AI-generated narratives (executive summary, key observations, risk assessment, recommendations).

**Q: What if my tests generate huge reports (1000+ tests)?**

A: The tool handles large reports efficiently:

- Use `--max-failures` to limit failures in the report (default: 20, use -1 to disable)
- Parallel LLM generation processes multiple sections concurrently
- Only detailed failures are included; passing tests are summarized
- Consider filtering tests before running or generating multiple focused reports

Example:

```bash
# Limit to top 10 failures
python -m qa_report_generator generate --json-report report.json --max-failures 10

# Disable failure limiting entirely
python -m qa_report_generator generate --json-report report.json --max-failures -1
```

**Q: Can I customize the report format/content?**

A: Yes, multiple ways:

1. **Custom Prompts**: Change LLM narrative style via `PROMPT_TEMPLATE_PATH`
2. **Custom Writers**: Create a writer plugin for HTML, PDF, JSON, etc.
3. **Custom Parsers**: Add support for other test formats (JUnit, TAP, etc.)
4. **Hooks**: Add post-processing, notifications, custom formatting

See the examples directory for extension references.

### Integration & Deployment

**Q: How do I integrate this with CI/CD?**

A: Example GitLab CI/Jenkins/GitHub Actions workflow (illustrative only for PoC validation):

```yaml
# .gitlab-ci.yml / .github/workflows/test.yml
test:
  script:
    # Run tests with JSON report
    - pytest --json-report --json-report-file=report.json

    # Validate configuration
    - qa-report-generator validate-config

    # Generate reports
    - qa-report-generator generate \
      --json-report report.json \
      --out reports/ \
      --env $CI_ENVIRONMENT_NAME \
      --build $CI_PIPELINE_ID \
      --commit $CI_COMMIT_SHA

  artifacts:
    paths:
      - reports/
    reports:
      junit: report.xml # If you have JUnit for GitLab
```

**Q: What are the performance considerations?**

A: Performance tips:

- **LLM calls**: Typically 2-5 seconds per section (4 sections total)
- **Parallel generation**: Enabled by default (4 sections concurrently)
- **Local vs Cloud**: Ollama (local) is slower but free; OpenAI is faster but costs $$
- **Model size**: Smaller models (1B-3B params) are faster than larger ones
- **Caching**: LLM doesn't cache between runs (each report is fresh)
- **Total time**: Usually 10-30 seconds for typical reports

For faster reports:

```bash
export MAX_PARALLEL_LLM_SECTIONS=4  # Increase parallelism
export LLM_TIMEOUT=60  # Reduce timeout
```

**Q: Is this tool suitable for production use?**

A: Current status: **Proof of Concept**.

**Not production-ready yet.** Before any production use, you should:

- Add broader integration coverage for adapter wiring and diff workflows.
- Establish performance benchmarks and capacity limits.
- Validate operational safeguards for LLM availability (timeouts, retries, fallbacks).
- Review plugin stability and compatibility guarantees.

Recommendation: Use in staging only for now, monitor LLM costs, and keep a fallback to `--no-llm` mode.

### Troubleshooting

**Q: Why am I getting "LLM generation failed" warnings?**

A: Common causes:

1. **Ollama not running**: Start with `ollama serve`
2. **Model not downloaded**: Run `ollama pull llama3.2`
3. **Wrong configuration**: Check `LLM_BASE_URL`, `LLM_MODEL`, and API key settings in `.env`
4. **Timeout**: Increase `LLM_TIMEOUT` for slow models
5. **API key**: If using OpenAI, provide valid `OPENAI_API_KEY`

The tool will gracefully generate reports without LLM sections. Check logs with `LOG_LEVEL=DEBUG`.

**Q: How do I debug configuration issues?**

A: Use the validate-config command:

```bash
# Check configuration and test LLM
python -m qa_report_generator validate-config

# Enable debug logging
LOG_LEVEL=DEBUG python -m qa_report_generator validate-config
```

This validates:

- Configuration validity
- Configuration warnings

**Q: Can I use this with test frameworks other than pytest?**

A: Currently only pytest JSON format is supported. To add support for other frameworks:

1. **Create a custom parser** implementing `ReportParser` interface
2. **Register it** with the plugin system
3. See the examples directory for reference implementations

Planned future support: JUnit XML, TAP format. Contributions welcome!

**Q: What if I need help or want to report a bug?**

A: Options:

- **Documentation**: Check README.md and the troubleshooting section
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions in GitHub Discussions
- **Logs**: Enable `LOG_LEVEL=DEBUG` to get detailed diagnostic information

### Cost & Resources

**Q: What are the costs of using cloud LLMs?**

A: Approximate costs (as of 2026):

- **Ollama**: Free (local, uses your CPU/GPU)
- **OpenAI GPT-4**: ~$0.03-0.06 per report (depending on length)
- **OpenAI GPT-3.5**: ~$0.001-0.002 per report
- **Azure OpenAI**: Similar to OpenAI pricing

Cost control:

```bash
export LLM_TEMPERATURE=0.0  # More deterministic (faster)
```

**Q: What system resources does this need?**

A: Minimal requirements:

- **CPU**: Any modern CPU (for Ollama: more cores = faster)
- **RAM**: 2GB for the tool + model requirements
  - Ollama 1B model: ~2GB RAM
  - Ollama 7B model: ~8GB RAM
- **Disk**: <100MB for tool, varies for models (1GB-10GB)
- **Network**: Only needed for cloud LLMs or downloading models

**Q: How do I choose the right temperature setting?**

A: Temperature guide:

- **0.0** (default): Most deterministic, factual, consistent - **Recommended for reports**
- **0.1-0.3**: Slightly varied outputs, still factual
- **0.5-0.7**: Balanced creativity and consistency
- **1.0+**: Creative, varied outputs (not recommended for factual reports)

Example:

```bash
export LLM_TEMPERATURE=0.0  # Factual reports
export LLM_TEMPERATURE=0.7  # More creative summaries
```

### Advanced Usage

**Q: Can I generate reports in formats other than Markdown?**

A: Yes! Create a custom writer plugin:

```python
from qa_report_generator.plugins import register_writer
from qa_report_generator.application.ports.output import ReportWriter

@register_writer("html")
class HTMLReportWriter(ReportWriter):
    def save_reports(self, facts, output_dir, narrative_generator=None):
        # Generate HTML reports
        pass
```

See `examples/custom_writer/json_writer.py` for a complete example.

**Q: How do I send notifications after report generation?**

A: Use lifecycle hooks:

```python
from qa_report_generator.plugins import register_hook

@register_hook("post_write")
def notify_teams(context):
    summary_path = context["summary_path"]
    facts = context["facts"]
    # Send Teams notification
```

See `examples/hooks/teams_notifier.py` for a complete example.

**Q: Can I run this in a Docker container?**

A: Yes! Example Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

# For Ollama (requires separate Ollama container)
ENV LLM_BASE_URL=http://ollama:11434/v1

ENTRYPOINT ["python", "-m", "qa_report_generator"]
```

Docker Compose:

```yaml
services:
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"

  reporting:
    build: .
    depends_on:
      - ollama
    volumes:
      - ./reports:/app/reports
```

## License

MIT

## Contributing

This is a proof-of-concept. Feedback welcome!
