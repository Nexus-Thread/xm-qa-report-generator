"""Tests with varying execution times."""

import time

import pytest
from calculator import add, factorial, multiply


def test_instant():
    """Very fast test - should complete in microseconds."""
    assert add(1, 1) == 2


def test_quick():
    """Quick test - under 0.1 seconds."""
    time.sleep(0.05)
    assert multiply(2, 3) == 6


def test_fast():
    """Fast test - around 0.1 seconds."""
    time.sleep(0.1)
    result = add(10, 20)
    assert result == 30


def test_medium():
    """Medium duration test - around 0.5 seconds."""
    time.sleep(0.5)
    result = factorial(10)
    assert result == 3628800


def test_slow():
    """Slow test - around 1 second."""
    time.sleep(1.0)
    total = 0
    for i in range(100):
        total = add(total, i)
    assert total == 4950


def test_very_slow():
    """Very slow test - around 2 seconds."""
    time.sleep(2.0)
    result = multiply(123, 456)
    assert result == 56088


def test_failing_slow():
    """Slow test that fails - around 1 second."""
    time.sleep(1.0)
    result = add(100, 200)
    assert result == 400  # Should be 300


class TestSlowSuite:
    """Test suite with various timing tests."""

    def test_suite_fast(self):
        """Fast test in suite."""
        time.sleep(0.05)
        assert True

    def test_suite_medium(self):
        """Medium test in suite."""
        time.sleep(0.3)
        assert multiply(5, 5) == 25

    def test_suite_slow(self):
        """Slow test in suite."""
        time.sleep(0.8)
        assert add(50, 50) == 100


@pytest.mark.parametrize("sleep_time", [0.1, 0.2, 0.3, 0.4])
def test_parametrized_timing(sleep_time):
    """Parametrized test with different sleep times."""
    time.sleep(sleep_time)
    assert True


def test_computation_intensive():
    """Test with actual computation instead of sleep."""
    # Calculate factorials for many numbers
    results = []
    for i in range(1, 100):
        results.append(factorial(i % 10))

    assert len(results) == 99
