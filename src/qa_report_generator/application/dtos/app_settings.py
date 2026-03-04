"""Application settings DTO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    """Runtime configuration consumed by application services."""

    log_level: str
    log_format: str
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    llm_timeout: float
    llm_max_retries: int
    llm_retry_backoff_factor: float
    llm_debug_json_enabled: bool
    llm_debug_json_dir: Path
