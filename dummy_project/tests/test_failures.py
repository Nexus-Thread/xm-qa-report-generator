"""Tests that fail with assertion errors."""

from calculator import add, divide, multiply, power, subtract


class TestIntentionalFailures:
    """Tests designed to fail with clear assertion errors."""

    def test_add_wrong_result(self):
        """Test addition with wrong expected value - will fail."""
        assert add(5, 3) == 10  # Should be 8

    def test_subtract_wrong_result(self):
        """Test subtraction with wrong expected value - will fail."""
        assert subtract(10, 3) == 5  # Should be 7

    def test_multiply_wrong_result(self):
        """Test multiplication with wrong expected value - will fail."""
        assert multiply(4, 5) == 25  # Should be 20

    def test_divide_wrong_result(self):
        """Test division with wrong expected value - will fail."""
        assert divide(10, 2) == 4  # Should be 5


def test_string_comparison_failure():
    """Test string comparison failure."""
    result = str(add(5, 3))
    assert result == "10"  # Should be "8"


def test_list_comparison_failure():
    """Test list comparison failure."""
    results = [add(1, 1), add(2, 2), add(3, 3)]
    expected = [2, 4, 8]  # Last one should be 6
    assert results == expected


def test_dict_comparison_failure():
    """Test dictionary comparison failure."""
    calculations = {
        "sum": add(5, 5),
        "product": multiply(5, 5),
        "difference": subtract(10, 5),
    }
    expected = {
        "sum": 10,
        "product": 25,
        "difference": 3,  # Should be 5
    }
    assert calculations == expected


def test_float_precision_failure():
    """Test float precision failure."""
    result = divide(10, 3)
    assert result == 3.33  # More precise value differs


def test_power_wrong_result(sample_numbers):
    """Test power with wrong expected value using fixture."""
    result = power(sample_numbers["c"], 3)
    assert result == 10  # Should be 8


def test_greater_than_failure():
    """Test greater than comparison failure."""
    result = add(5, 5)
    assert result > 12  # 10 is not greater than 12


def test_less_than_failure():
    """Test less than comparison failure."""
    result = multiply(5, 5)
    assert result < 20  # 25 is not less than 20


def test_contains_failure():
    """Test contains check failure."""
    result_str = f"Result: {add(5, 5)}"
    assert "15" in result_str  # Should be "10"


def test_type_assertion_failure():
    """Test type assertion failure."""
    result = add(5.5, 3.5)
    assert isinstance(result, int)  # Result is float


def test_not_none_failure():
    """Test not None assertion failure."""
    result = None  # Simulating a failure case
    assert result is not None
    assert result == 100


def test_boolean_assertion_failure():
    """Test boolean assertion failure."""
    result = add(5, 5)
    assert result % 3 == 0  # 10 is not divisible by 3
