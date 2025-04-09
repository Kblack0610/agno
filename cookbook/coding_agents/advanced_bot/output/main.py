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
    # If it's an integer or a float that equals its integer value, display as int
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    
    # For floats, limit to 6 decimal places and remove trailing zeros
    if isinstance(result, float):
        formatted = f"{result:.6f}".rstrip('0').rstrip('.')
        return formatted
    
    return str(result)


def display_welcome():
    """Display welcome message and instructions."""
    print("==================================")
    print("   Simple Calculator Application  ")
    print("==================================")
    print("Operations: + (add), - (subtract), * (multiply), / (divide)")
    print("Enter 'exit' or 'q' to quit")
    print()


def parse_input(user_input):
    """
    Parse the user input string into operands and operator.
    
    Args:
        user_input (str): The input string (e.g., "5 + 3")
        
    Returns:
        tuple: (first_number, operator, second_number) or None if parsing fails
    """
    try:
        # Split the input by spaces
        parts = user_input.strip().split()
        
        if len(parts) != 3:
            print("Error: Please use format 'number operator number'")
            return None
            
        first_number = float(parts[0])
        operator = parts[1]
        second_number = float(parts[2])
        
        # Validate operator
        if operator not in ['+', '-', '*', '/']:
            print(f"Error: Unsupported operator '{operator}'")
            print("Supported operators: +, -, *, /")
            return None
            
        return first_number, operator, second_number
    except ValueError:
        print("Error: Please enter valid numbers")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def calculate(first_number, operator, second_number):
    """
    Perform the calculation based on the operator.
    
    Args:
        first_number (float): First number
        operator (str): Operator ('+', '-', '*', '/')
        second_number (float): Second number
        
    Returns:
        float: Result of the calculation or None if operation fails
    """
    try:
        if operator == '+':
            return add(first_number, second_number)
        elif operator == '-':
            return subtract(first_number, second_number)
        elif operator == '*':
            return multiply(first_number, second_number)
        elif operator == '/':
            return divide(first_number, second_number)
    except ZeroDivisionError:
        print("Error: Division by zero is not allowed")
        return None
    except Exception as e:
        print(f"Error during calculation: {str(e)}")
        return None


def calculator_loop():
    """Run the interactive calculator loop."""
    display_welcome()
    
    while True:
        # Get user input
        user_input = input("Enter calculation: ").strip()
        
        # Check for exit command
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Thank you for using the calculator!")
            break
            
        # Process the input
        parsed_input = parse_input(user_input)
        if parsed_input:
            first_number, operator, second_number = parsed_input
            result = calculate(first_number, operator, second_number)
            
            if result is not None:
                formatted_result = format_result(result)
                print(f"Result: {formatted_result}")
        
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
