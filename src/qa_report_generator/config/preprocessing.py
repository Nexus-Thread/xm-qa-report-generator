"""Preprocessing profile constants for report generation configuration."""

from enum import StrEnum
from typing import TypedDict


class PreprocessingProfile(StrEnum):
    """Predefined preprocessing profiles for report generation."""

    MINIMAL = "minimal"
    BALANCED = "balanced"
    DETAILED = "detailed"


class ProfileDefaults(TypedDict):
    """Field overrides applied when a preprocessing profile is active."""

    max_output_lines_per_failure: int
    enable_failure_grouping: bool
    failure_clustering_threshold: float
    max_failures_for_detailed_prompt: int


PROFILE_DEFAULTS: dict[str, ProfileDefaults] = {
    PreprocessingProfile.MINIMAL: {
        "max_output_lines_per_failure": 10,
        "enable_failure_grouping": False,
        "failure_clustering_threshold": 0.85,
        "max_failures_for_detailed_prompt": 5,
    },
    PreprocessingProfile.BALANCED: {
        "max_output_lines_per_failure": 20,
        "enable_failure_grouping": True,
        "failure_clustering_threshold": 0.7,
        "max_failures_for_detailed_prompt": 10,
    },
    PreprocessingProfile.DETAILED: {
        "max_output_lines_per_failure": 30,
        "enable_failure_grouping": True,
        "failure_clustering_threshold": 0.6,
        "max_failures_for_detailed_prompt": 15,
    },
}
