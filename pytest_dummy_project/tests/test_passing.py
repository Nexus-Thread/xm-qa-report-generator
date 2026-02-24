"""Tests that pass successfully."""

from calculator import add, divide, factorial, multiply, power, square_root, subtract


class TestBasicOperations:
    """Test basic calculator operations - all passing."""

    def test_add_positive_numbers(self):
        """Test adding two positive numbers."""
        assert add(5, 3) == 8

    def test_add_negative_numbers(self):
        """Test adding two negative numbers."""
        assert add(-5, -3) == -8

    def test_subtract_positive_numbers(self):
        """Test subtracting positive numbers."""
        assert subtract(10, 3) == 7

    def test_multiply_positive_numbers(self):
        """Test multiplying positive numbers."""
        assert multiply(4, 5) == 20

    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        assert multiply(100, 0) == 0

    def test_divide_positive_numbers(self):
        """Test dividing positive numbers."""
        assert divide(10, 2) == 5


class TestAdvancedOperations:
    """Test advanced calculator operations - all passing."""

    def test_power_positive_base(self):
        """Test power with positive base."""
        assert power(2, 3) == 8

    def test_power_zero_exponent(self):
        """Test power with zero exponent."""
        assert power(5, 0) == 1

    def test_square_root_positive(self):
        """Test square root of positive number."""
        assert square_root(16) == 4

    def test_square_root_zero(self):
        """Test square root of zero."""
        assert square_root(0) == 0

    def test_factorial_zero(self):
        """Test factorial of zero."""
        assert factorial(0) == 1

    def test_factorial_positive(self):
        """Test factorial of positive number."""
        assert factorial(5) == 120


def test_add_with_fixture(sample_numbers):
    """Test add using fixture."""
    result = add(sample_numbers["a"], sample_numbers["b"])
    assert result == 15.0


def test_multiply_with_fixture(sample_numbers):
    """Test multiply using fixture."""
    result = multiply(sample_numbers["a"], sample_numbers["c"])
    assert result == 20.0


def test_chain_operations():
    """Test chaining multiple operations."""
    result = add(multiply(2, 3), divide(10, 2))
    assert result == 11


def test_complex_calculation():
    """Test complex calculation combining operations."""
    # (5 + 3) * 2 - 4 = 12
    step1 = add(5, 3)
    step2 = multiply(step1, 2)
    step3 = subtract(step2, 4)
    assert step3 == 12
