"""Unit tests for logging configuration."""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path
from typing import cast

from qa_report_generator.application.dtos import AppSettings
from qa_report_generator.config.logging_config import setup_logging


def _build_settings(*, log_level: str = "INFO", log_format: str = "simple") -> AppSettings:
    """Build application settings for logging tests."""
    return AppSettings(
        log_level=log_level,
        log_format=log_format,
        llm_model="gpt-test",
        llm_base_url="https://example.test/v1",
        llm_api_key="secret",
        llm_timeout=30.0,
        llm_max_retries=2,
        llm_retry_backoff_factor=2.0,
        llm_debug_json_enabled=False,
        llm_debug_json_dir=Path("out/debug/llm"),
    )


def _get_stream_handler() -> logging.StreamHandler[io.TextIOBase]:
    """Return the configured root stream handler."""
    handler = logging.getLogger().handlers[0]
    return cast("logging.StreamHandler[io.TextIOBase]", handler)


def test_setup_logging_configures_simple_format() -> None:
    """Simple logging setup emits formatted text."""
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    stream = io.StringIO()

    try:
        setup_logging(_build_settings(log_level="WARNING", log_format="simple"))

        handler = _get_stream_handler()
        handler.setStream(stream)

        logger = logging.getLogger("qa_report_generator.tests.simple")
        logger.warning("simple message")

        output = stream.getvalue()
        assert root_logger.level == logging.WARNING
        assert "WARNING" in output
        assert "simple message" in output
        assert "qa_report_generator.tests.simple" in output
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
        root_logger.setLevel(original_level)


def test_setup_logging_configures_json_format_with_extra_fields() -> None:
    """JSON logging setup emits structured extra fields."""
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    stream = io.StringIO()

    try:
        setup_logging(_build_settings(log_level="INFO", log_format="json"))

        handler = _get_stream_handler()
        handler.setStream(stream)

        logger = logging.getLogger("qa_report_generator.tests.json")
        logger.info("json message", extra={"component": "test", "service": "demo"})

        payload = json.loads(stream.getvalue())
        assert payload["level"] == "INFO"
        assert payload["logger"] == "qa_report_generator.tests.json"
        assert payload["message"] == "json message"
        assert payload["component"] == "test"
        assert payload["service"] == "demo"
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
        root_logger.setLevel(original_level)


def test_setup_logging_reconfigures_existing_root_handlers() -> None:
    """Repeated setup replaces previous root handlers and level."""
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    first_stream = io.StringIO()
    second_stream = io.StringIO()

    try:
        setup_logging(_build_settings(log_level="INFO", log_format="simple"))
        first_handler = _get_stream_handler()
        first_handler.setStream(first_stream)

        setup_logging(_build_settings(log_level="ERROR", log_format="json"))
        second_handler = _get_stream_handler()
        second_handler.setStream(second_stream)

        logger = logging.getLogger("qa_report_generator.tests.reconfigure")
        logger.warning("ignored warning")
        logger.error("error message", extra={"component": "reconfigure"})

        assert len(root_logger.handlers) == 1
        assert root_logger.level == logging.ERROR
        assert first_stream.getvalue() == ""

        payload = json.loads(second_stream.getvalue())
        assert payload["level"] == "ERROR"
        assert payload["message"] == "error message"
        assert payload["component"] == "reconfigure"
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
        root_logger.setLevel(original_level)
