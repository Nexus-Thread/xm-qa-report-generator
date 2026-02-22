"""Application-level settings DTO."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    """Application configuration values."""

    log_level: str
    log_format: str
    prompt_template_path: str | None
    llm_model: str
    llm_base_url: str
    llm_api_key: str
    llm_temperature: float | None
    llm_reasoning_effort: str | None
    llm_timeout: float
    llm_max_retries: int
    llm_retry_backoff_factor: float
    max_parallel_llm_sections: int
    max_output_lines_per_failure: int
    enable_failure_grouping: bool
    failure_clustering_threshold: float
    max_failures_for_detailed_prompt: int
    preprocessing_profile: str | None
    plugin_modules: tuple[str, ...]
