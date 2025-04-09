"""
Utility functions for the calculator application.

This module provides the core arithmetic operations and formatting utilities.
"""

from typing import Union, Optional, Tuple


# Type alias for numeric values
Number = Union[int, float]


def add(a: Number, b: Number) -> Number:
    """
    Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The sum of a and b
    """
    return a + b


def subtract(a: Number, b: Number) -> Number:
    """
    Subtract the second number from the first.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The difference between a and b
    """
    return a - b


def multiply(a: Number, b: Number) -> Number:
    """
    Multiply two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        The product of a and b
    """
    return a * b


def divide(a: Number, b: Number) -> Number:
    """
    Divide the first number by the second.
    
    Args:
        a: Numerator
        b: Denominator
        
    Returns:
        The quotient of a divided by b
        
    Raises:
        ZeroDivisionError: If b is zero
    """
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def format_result(result: Number) -> str:
    """
    Format the result for display.
    
    Args:
        result: The number to format
        
    Returns:
        A formatted string representation of the number
    """
    # If it's an integer or a float that equals its integer value, display as int
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    
    # For floats, limit to 6 decimal places and remove trailing zeros
    if isinstance(result, float):
        formatted = f"{result:.6f}".rstrip('0').rstrip('.')
        return formatted
    
    return str(result)
