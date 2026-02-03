"""Basic calculator operations."""


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide a by b.

    Raises:
        ValueError: If b is zero

    """
    if b == 0:
        msg = "Cannot divide by zero"
        raise ValueError(msg)
    return a / b
