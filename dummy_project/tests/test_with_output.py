"""Tests that produce stdout, stderr, and log output."""

import logging
import sys

from calculator import add, divide, multiply

# Configure logging for these tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_with_stdout_output():
    """Test that prints to stdout."""
    print("Starting calculation...")
    result = add(5, 3)
    print(f"Calculation result: {result}")
    print("Calculation completed successfully")
    assert result == 8


def test_with_stderr_output():
    """Test that prints to stderr."""
    print("This is an error message", file=sys.stderr)
    result = multiply(4, 5)
    print(f"Error level: {result}", file=sys.stderr)
    assert result == 20


def test_with_log_output():
    """Test that uses logging."""
    logger.info("Starting test execution")
    result = divide(10, 2)
    logger.info(f"Division result: {result}")
    logger.warning("This is a warning message")
    assert result == 5


def test_with_mixed_output():
    """Test with stdout, stderr, and logging."""
    print("Standard output message")
    logger.info("Info log message")
    print("Error output message", file=sys.stderr)
    logger.error("Error log message")

    result = add(10, 20)
    print(f"Result from stdout: {result}")
    logger.info(f"Result from logger: {result}")

    assert result == 30


def test_with_multiline_output():
    """Test with multiline output."""
    print("=" * 50)
    print("CALCULATION REPORT")
    print("=" * 50)
    print("Operation: Addition")
    print("Operands: 15, 25")

    result = add(15, 25)

    print(f"Result: {result}")
    print("=" * 50)
    print("Report completed")

    assert result == 40


def test_failing_with_output():
    """Test that fails but has output."""
    print("Starting calculation that will fail...")
    logger.info("Attempting division")

    result = divide(10, 2)
    print(f"Got result: {result}")

    # This assertion will fail
    assert result == 10  # Should be 5


def test_with_debug_output():
    """Test with debug level logging."""
    logger.debug("Debug message - very detailed")
    logger.info("Info message - general information")
    logger.warning("Warning message - something to watch")

    result = multiply(3, 7)
    logger.info(f"Multiplication result: {result}")

    assert result == 21


class TestOutputInSetup:
    """Test class with output in setup/teardown."""

    def setup_method(self):
        """Setup with output."""
        print("Setup: Initializing test environment")
        logger.info("Setup: Test environment ready")

    def teardown_method(self):
        """Teardown with output."""
        print("Teardown: Cleaning up test environment")
        logger.info("Teardown: Test environment cleaned")

    def test_with_setup_teardown_output(self):
        """Test that has output in all phases."""
        print("Test: Executing test logic")
        logger.info("Test: Running assertions")
        result = add(100, 200)
        assert result == 300


def test_error_with_output():
    """Test that errors but has output."""
    print("This test will raise an error")
    logger.error("About to trigger an error condition")

    # This will raise an error
    result = divide(10, 0)
    assert result == 5
