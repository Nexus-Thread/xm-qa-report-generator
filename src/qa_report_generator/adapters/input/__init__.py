"""Input adapters - Entry points that drive the application.

Input adapters (also called "driving" adapters) are the entry points that trigger
application logic. They receive external requests and translate them into use case
invocations. Examples include CLI interfaces, REST APIs, or message queue consumers.

Currently available:
- **CliAdapter**: Command-line interface for generating test reports
"""

from qa_report_generator.adapters.input.cli_adapter import CliAdapter

__all__ = [
    "CliAdapter",
]
