"""Logging configuration for the reporting PoC."""

import logging
import sys
from collections.abc import Mapping
from datetime import UTC
from typing import Any

from qa_report_generator.application.dtos import AppSettings


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string

        """
        import json
        from datetime import datetime

        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present (dynamically added to LogRecord)
        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, Mapping):
            log_data.update(extra_fields)

        return json.dumps(log_data)


def setup_logging(config: AppSettings) -> None:
    """Configure logging based on configuration settings.

    Args:
        config: Configuration object.

    """
    # Get log level
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)

    # Set formatter based on config
    if config.log_format.lower() == "json":
        formatter: logging.Formatter = JsonFormatter()
    else:
        # Simple human-readable format
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set log level for our package
    package_logger = logging.getLogger("qa_report_generator")
    package_logger.setLevel(log_level)

    # Reduce noise from third-party libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
