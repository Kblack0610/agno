
import pytest
from fibonacci import calculate_fibonacci

def test_calculate_fibonacci_empty():
    """Test fibonacci with n=0."""
    assert calculate_fibonacci(0) == []

def test_calculate_fibonacci_one():
    """Test fibonacci with n=1."""
    assert calculate_fibonacci(1) == [0]

def test_calculate_fibonacci_two():
    """Test fibonacci with n=2."""
    assert calculate_fibonacci(2) == [0, 1]

def test_calculate_fibonacci_five():
    """Test fibonacci with n=5."""
    assert calculate_fibonacci(5) == [0, 1, 1, 2, 3]

def test_calculate_fibonacci_ten():
    """Test fibonacci with n=10."""
    assert calculate_fibonacci(10) == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
