"""Parametrized tests with various outcomes."""

import pytest
from calculator import add, divide, multiply, power, square_root


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (2, 3, 5),  # Pass
        (10, 5, 15),  # Pass
        (0, 0, 0),  # Pass
        (-5, 5, 0),  # Pass
        (100, 200, 300),  # Pass
        (7, 8, 14),  # Fail - should be 15
    ],
)
def test_add_parametrized(a, b, expected):
    """Test addition with multiple parameter sets."""
    assert add(a, b) == expected


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (2, 3, 6),  # Pass
        (5, 5, 25),  # Pass
        (10, 0, 0),  # Pass
        (1, 100, 100),  # Pass
        (4, 4, 15),  # Fail - should be 16
        (3, 7, 22),  # Fail - should be 21
    ],
)
def test_multiply_parametrized(a, b, expected):
    """Test multiplication with multiple parameter sets."""
    assert multiply(a, b) == expected


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (10, 2, 5),  # Pass
        (100, 10, 10),  # Pass
        (15, 3, 5),  # Pass
        (20, 4, 6),  # Fail - should be 5
    ],
)
def test_divide_parametrized(a, b, expected):
    """Test division with multiple parameter sets."""
    assert divide(a, b) == expected


@pytest.mark.parametrize(
    ("base", "exp", "expected"),
    [
        (2, 3, 8),  # Pass
        (5, 2, 25),  # Pass
        (10, 0, 1),  # Pass
        (3, 4, 81),  # Pass
        (2, 8, 255),  # Fail - should be 256
    ],
)
def test_power_parametrized(base, exp, expected):
    """Test power with multiple parameter sets."""
    assert power(base, exp) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (4, 2),  # Pass
        (9, 3),  # Pass
        (16, 4),  # Pass
        (25, 5),  # Pass
        (36, 7),  # Fail - should be 6
    ],
)
def test_square_root_parametrized(value, expected):
    """Test square root with multiple parameter sets."""
    assert square_root(value) == expected


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (10, 0),  # Will raise ValueError
        (5, 0),  # Will raise ValueError
        (100, 0),  # Will raise ValueError
    ],
)
def test_divide_by_zero_parametrized(a, b):
    """Test division by zero with multiple parameter sets - all should error."""
    divide(a, b)


@pytest.mark.parametrize(
    "value",
    [
        -4,  # Will raise ValueError
        -9,  # Will raise ValueError
        -16,  # Will raise ValueError
    ],
)
def test_square_root_negative_parametrized(value):
    """Test square root of negative numbers - all should error."""
    square_root(value)


class TestParametrizedClass:
    """Class with parametrized tests."""

    @pytest.mark.parametrize("x", [1, 2, 3, 4, 5])
    def test_positive_numbers(self, x):
        """Test that all inputs are positive."""
        assert x > 0

    @pytest.mark.parametrize(
        ("operation", "a", "b", "expected"),
        [
            ("add", 5, 3, 8),
            ("multiply", 5, 3, 15),
            ("add", 10, 10, 20),
            ("multiply", 10, 10, 99),  # Fail - should be 100
        ],
    )
    def test_mixed_operations(self, operation, a, b, expected):
        """Test different operations with parameters."""
        if operation == "add":
            result = add(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        else:
            msg = f"Unknown operation: {operation}"
            raise ValueError(msg)

        assert result == expected
