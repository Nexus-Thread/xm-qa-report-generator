"""Application-level settings DTO."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AppSettings:
    """Application configuration values."""

    log_level: str = "INFO"
    log_format: str = "simple"
    prompt_template_path: str | None = None
    llm_model: str = "gpt-5.2"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = "not-needed"
    llm_temperature: float | None = None
    llm_reasoning_effort: str | None = None
    llm_timeout: float = 100.0
    llm_max_retries: int = 3
    llm_retry_backoff_factor: float = 2.0
    max_parallel_llm_sections: int = 1
    max_output_lines_per_failure: int = 20
    enable_failure_grouping: bool = True
    failure_clustering_threshold: float = 0.7
    max_failures_for_detailed_prompt: int = 10
    preprocessing_profile: str | None = None
    plugin_modules: tuple[str, ...] = field(default_factory=tuple)
