"""Application settings DTO."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    """Runtime configuration consumed by application services."""

    llm_api_key: str = field()
    log_level: str = field(default="INFO")
    log_format: str = field(default="simple")
    llm_model: str = field(default="gpt-5.2")
    llm_base_url: str = field(default="https://api.openai.com/v1")
    llm_timeout: float = field(default=100.0)
    llm_max_retries: int = field(default=3)
    llm_retry_backoff_factor: float = field(default=2.0)
    llm_debug_json_enabled: bool = field(default=False)
    llm_debug_json_dir: Path = field(default_factory=lambda: Path("out/debug/llm"))
    model_debug_json_enabled: bool = field(default=True)
    model_debug_json_dir: Path = field(default_factory=lambda: Path("out/debug/models"))
