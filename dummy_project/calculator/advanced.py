"""Advanced calculator operations."""

import math


def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent.

    Raises:
        ValueError: For invalid operations (e.g., negative base with fractional exponent)

    """
    try:
        return base**exponent
    except ValueError as e:
        msg = f"Invalid power operation: {e}"
        raise ValueError(msg) from e


def square_root(x: float) -> float:
    """Calculate square root of x.

    Raises:
        ValueError: If x is negative

    """
    if x < 0:
        msg = "Cannot calculate square root of negative number"
        raise ValueError(msg)
    return math.sqrt(x)


def factorial(n: int) -> int:
    """Calculate factorial of n.

    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer

    """
    if not isinstance(n, int):
        msg = "Factorial only accepts integers"
        raise TypeError(msg)
    if n < 0:
        msg = "Factorial not defined for negative numbers"
        raise ValueError(msg)
    return math.factorial(n)
