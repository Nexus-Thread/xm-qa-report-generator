"""Application settings DTO."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Runtime configuration consumed by application services."""

    llm_api_key: str
    log_level: str = "INFO"
    log_format: str = "simple"
    llm_model: str = "gpt-5.2"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_timeout: float = 100.0
    llm_max_retries: int = 3
    llm_max_concurrency: int = 4
    llm_retry_backoff_factor: float = 2.0
    llm_debug_json_enabled: bool = False
    llm_debug_json_dir: Path = field(default_factory=lambda: Path("out/debug/llm"))
    model_debug_json_enabled: bool = True
    model_debug_json_dir: Path = field(default_factory=lambda: Path("out/debug/models"))
