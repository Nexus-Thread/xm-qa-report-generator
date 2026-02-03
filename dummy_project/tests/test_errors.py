"""Tests that raise errors and exceptions."""

import pytest
from calculator import divide, factorial, power, square_root


class TestRuntimeErrors:
    """Tests that raise various runtime errors."""

    def test_divide_by_zero(self):
        """Test division by zero raises ValueError."""
        divide(10, 0)  # Will raise ValueError

    def test_square_root_negative(self):
        """Test square root of negative number raises ValueError."""
        square_root(-5)  # Will raise ValueError

    def test_factorial_negative(self):
        """Test factorial of negative number raises ValueError."""
        factorial(-5)  # Will raise ValueError

    def test_factorial_float(self):
        """Test factorial of float raises TypeError."""
        factorial(5.5)  # Will raise TypeError


def test_type_error_string_addition():
    """Test type error when adding string to number."""
    from calculator import add

    add("5", 3)  # Will raise TypeError


def test_attribute_error():
    """Test attribute error."""
    from calculator import add

    result = add(5, 3)
    result.non_existent_method()  # Will raise AttributeError


def test_index_error():
    """Test index error."""
    my_list = [1, 2, 3]
    value = my_list[10]  # Will raise IndexError


def test_key_error():
    """Test key error."""
    my_dict = {"a": 1, "b": 2}
    value = my_dict["c"]  # Will raise KeyError


def test_value_error_custom():
    """Test custom value error."""
    msg = "This is a custom error message for testing"
    raise ValueError(msg)


def test_zero_division_error():
    """Test zero division error."""
    result = 10 / 0  # Will raise ZeroDivisionError


def test_name_error():
    """Test name error with undefined variable."""
    result = undefined_variable + 5  # Will raise NameError


def test_assertion_with_exception():
    """Test that catches exception but still fails."""
    with pytest.raises(ValueError):
        divide(10, 2)  # This won't raise ValueError, so test fails


def test_runtime_error():
    """Test runtime error."""
    msg = "Runtime error occurred during calculation"
    raise RuntimeError(msg)


def test_import_error():
    """Test import error."""


def test_overflow_error():
    """Test overflow with very large power."""
    power(10.0, 100000)  # May raise OverflowError
