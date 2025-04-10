#!/usr/bin/env python3
"""
Calculator Application

A command-line calculator that performs basic arithmetic operations.
This module provides a user interface for the calculator functionality.
"""

import sys
import os
from typing import Union, Optional, Tuple

# Type alias for numeric values
Number = Union[int, float]

# Define utility functions directly in main.py to avoid import issues
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
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    if isinstance(result, float):
        # Remove trailing zeros and decimal point if not needed
        return f"{result:.6f}".rstrip('0').rstrip('.')
    return str(result)


def display_welcome():
    """Display welcome message and instructions."""
    print("==================================")
    print("   Simple Calculator Application  ")
    print("==================================")
    print("Operations: + (add), - (subtract), * (multiply), / (divide)")
    print("Enter 'exit' or 'q' to quit")
    print()


def parse_input(user_input: str) -> Tuple[float, str, float]:
    """
    Parse the user input string into operands and operator.
    
    Args:
        user_input (str): The input string (e.g., "5 + 3")
        
    Returns:
        tuple: (first_number, operator, second_number)
        
    Raises:
        ValueError: If input format is invalid or contains unsupported operators
    """
    # Split the input by spaces
    parts = user_input.split()
    
    # Ensure we have exactly 3 parts (operand, operator, operand)
    if len(parts) != 3:
        raise ValueError("Invalid input format. Please use: number operator number")
    
    # Extract values
    first_str, operator, second_str = parts
    
    # Check operator
    valid_operators = ['+', '-', '*', '/']
    if operator not in valid_operators:
        raise ValueError(f"Unsupported operator '{operator}'. Supported operators: {', '.join(valid_operators)}")
    
    # Convert operands to float
    try:
        first_number = float(first_str)
        second_number = float(second_str)
    except ValueError:
        raise ValueError("Invalid numbers. Please enter numeric values.")
    
    return (first_number, operator, second_number)


def calculate(first_number: float, operator: str, second_number: float) -> float:
    """
    Perform the calculation based on the operator.
    
    Args:
        first_number (float): First number
        operator (str): Operator ('+', '-', '*', '/')
        second_number (float): Second number
        
    Returns:
        float: Result of the calculation
        
    Raises:
        ValueError: If operator is not supported
        ZeroDivisionError: If division by zero is attempted
    """
    if operator == '+':
        return add(first_number, second_number)
    elif operator == '-':
        return subtract(first_number, second_number)
    elif operator == '*':
        return multiply(first_number, second_number)
    elif operator == '/':
        return divide(first_number, second_number)
    else:
        raise ValueError(f"Unsupported operator: {operator}")


def calculator_loop():
    """Run the interactive calculator loop."""
    display_welcome()
    
    while True:
        try:
            # Get user input
            user_input = input("Enter calculation: ").strip()
            
            # Check for exit command
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Thank you for using the calculator!")
                break
                
            # Process the input
            first_number, operator, second_number = parse_input(user_input)
            result = calculate(first_number, operator, second_number)
            
            formatted_result = format_result(result)
            print(f"Result: {formatted_result}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print()  # Empty line for readability


def main():
    """Main entry point for the application."""
    try:
        calculator_loop()
    except KeyboardInterrupt:
        print("\nCalculator terminated.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
