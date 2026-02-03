"""Tests that are skipped with various reasons."""

import sys

import pytest
from calculator import add, factorial, multiply


@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    """Test for a feature not yet implemented."""


@pytest.mark.skip(reason="Waiting for bug fix in dependency")
def test_with_known_bug():
    """Test that depends on external bug fix."""
    assert add(5, 3) == 8


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Requires Python 3.12+")
def test_python_version_specific():
    """Test that only runs on Python 3.12+."""
    assert add(1, 1) == 2


@pytest.mark.skipif(sys.platform == "win32", reason="Not supported on Windows")
def test_unix_only_feature():
    """Test that only runs on Unix-like systems."""
    assert multiply(2, 3) == 6


@pytest.mark.skip(reason="Performance test - run manually")
def test_performance_benchmark():
    """Performance test that should be run manually."""
    for i in range(1000):
        add(i, i + 1)


def test_conditional_skip():
    """Test with conditional skip based on runtime check."""
    import os

    if os.getenv("RUN_EXPENSIVE_TESTS") != "1":
        pytest.skip("Expensive tests not enabled")

    # This would run if environment variable is set
    result = factorial(100)
    assert result > 0


@pytest.mark.skip(reason="Flaky test - needs investigation")
def test_flaky_behavior():
    """Test that sometimes fails - skipped until fixed."""
    import random

    assert random.choice([True, False])


class TestSkippedSuite:
    """Suite of tests that are all skipped."""

    @pytest.mark.skip(reason="Suite under development")
    def test_feature_one(self):
        """First feature test."""

    @pytest.mark.skip(reason="Suite under development")
    def test_feature_two(self):
        """Second feature test."""

    @pytest.mark.skip(reason="Suite under development")
    def test_feature_three(self):
        """Third feature test."""
