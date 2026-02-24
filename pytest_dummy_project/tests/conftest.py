"""Pytest configuration and fixtures for calculator tests."""

import pytest


@pytest.fixture
def sample_numbers():
    """Provide sample numbers for testing."""
    return {"a": 10.0, "b": 5.0, "c": 2.0}


@pytest.fixture
def zero():
    """Provide zero for division tests."""
    return 0.0


@pytest.fixture
def negative_number():
    """Provide a negative number for testing."""
    return -5.0


@pytest.fixture
def positive_integers():
    """Provide positive integers for factorial tests."""
    return [0, 1, 5, 10]
