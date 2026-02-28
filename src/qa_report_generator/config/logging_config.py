"""Central logging configuration helpers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_report_generator.application.dtos import AppSettings


def setup_logging(config: AppSettings) -> None:
    """Configure root logger from application settings."""
    level = getattr(logging, config.log_level.upper(), logging.INFO)
    if config.log_format == "json":
        logging.basicConfig(level=level, format='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}')
        return
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
