"""Unit tests for preprocessing profiles."""

from __future__ import annotations

from qa_report_generator.adapters.input.env import EnvSettings
from qa_report_generator.config import PreprocessingProfile


def test_profile_defaults_apply_when_fields_unset() -> None:
    """Profiles should apply defaults when fields are unset."""
    config = EnvSettings(preprocessing_profile=PreprocessingProfile.MINIMAL)
    config.apply_profile_defaults()

    assert config.max_output_lines_per_failure == 10
    assert config.enable_failure_grouping is False
    assert config.failure_clustering_threshold == 0.85
    assert config.max_failures_for_detailed_prompt == 5


def test_profile_does_not_override_explicit_settings() -> None:
    """Profiles should not override explicitly provided settings."""
    config = EnvSettings(
        preprocessing_profile=PreprocessingProfile.DETAILED,
        max_output_lines_per_failure=5,
        failure_clustering_threshold=0.9,
    )
    config.apply_profile_defaults()

    assert config.max_output_lines_per_failure == 5
    assert config.failure_clustering_threshold == 0.9
    assert config.max_failures_for_detailed_prompt == 15
