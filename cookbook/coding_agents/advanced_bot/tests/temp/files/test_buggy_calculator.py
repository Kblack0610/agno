
import pytest
from buggy_calculator import Calculator

@pytest.fixture
def calculator():
    return Calculator()

def test_add(calculator):
    """Test addition."""
    assert calculator.add(2, 3) == 5
    assert calculator.add(-1, 1) == 0
    assert calculator.add(0, 0) == 0

def test_subtract(calculator):
    """Test subtraction."""
    assert calculator.subtract(5, 3) == 2
    assert calculator.subtract(1, 1) == 0
    assert calculator.subtract(0, 5) == -5

def test_multiply(calculator):
    """Test multiplication."""
    assert calculator.multiply(2, 3) == 6
    assert calculator.multiply(-1, 3) == -3
    assert calculator.multiply(0, 5) == 0

def test_divide(calculator):
    """Test division."""
    assert calculator.divide(6, 3) == 2
    assert calculator.divide(5, 2) == 2.5
    assert calculator.divide(0, 5) == 0
    
    with pytest.raises(ZeroDivisionError):
        calculator.divide(5, 0)
