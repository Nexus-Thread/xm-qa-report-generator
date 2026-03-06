"""Central logging configuration helpers."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.application.dtos import AppSettings


_RESERVED_LOG_RECORD_FIELDS = frozenset(logging.makeLogRecord({}).__dict__)


class JsonLogFormatter(logging.Formatter):
    """Format log records as JSON with standard and extra fields."""

    def format(self, record: logging.LogRecord) -> str:
        """Return the log record serialized as JSON."""
        payload: dict[str, object] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _RESERVED_LOG_RECORD_FIELDS or key in payload:
                continue
            payload[key] = value

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def _build_handler(config: AppSettings) -> logging.Handler:
    """Create a stream handler for the configured log format."""
    handler = logging.StreamHandler()
    if config.log_format == "json":
        handler.setFormatter(JsonLogFormatter())
        return handler

    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    return handler


def setup_logging(config: AppSettings) -> None:
    """Configure root logger from application settings."""
    level = getattr(logging, config.log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()
    root_logger.setLevel(level)
    root_logger.addHandler(_build_handler(config))
