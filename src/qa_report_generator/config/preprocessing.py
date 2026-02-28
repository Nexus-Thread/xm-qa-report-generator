"""Preprocessing profile defaults."""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


class PreprocessingDefaults(TypedDict):
    """Typed preprocessing defaults for one profile."""

    max_output_lines_per_failure: int
    enable_failure_grouping: bool
    failure_clustering_threshold: float
    max_failures_for_detailed_prompt: int


class PreprocessingProfile(StrEnum):
    """Supported preprocessing profile presets."""

    MINIMAL = "minimal"
    BALANCED = "balanced"
    DETAILED = "detailed"


PROFILE_DEFAULTS: dict[PreprocessingProfile, PreprocessingDefaults] = {
    PreprocessingProfile.MINIMAL: {
        "max_output_lines_per_failure": 10,
        "enable_failure_grouping": True,
        "failure_clustering_threshold": 0.8,
        "max_failures_for_detailed_prompt": 5,
    },
    PreprocessingProfile.BALANCED: {
        "max_output_lines_per_failure": 20,
        "enable_failure_grouping": True,
        "failure_clustering_threshold": 0.7,
        "max_failures_for_detailed_prompt": 10,
    },
    PreprocessingProfile.DETAILED: {
        "max_output_lines_per_failure": 50,
        "enable_failure_grouping": False,
        "failure_clustering_threshold": 0.6,
        "max_failures_for_detailed_prompt": 30,
    },
}
