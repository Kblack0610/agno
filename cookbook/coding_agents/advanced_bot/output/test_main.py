#!/usr/bin/env python3
"""
Unit tests for the calculator application.

This module contains tests for the calculator's functionality.
"""

import unittest
import io
import sys
import os
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

# Add pytest markers for better compatibility
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

# Add the current directory to the path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main module
import main
from main import (
    add, subtract, multiply, divide, format_result, 
    parse_input, calculate, calculator_loop
)

class TestCalculatorUtils(unittest.TestCase):
    """Test cases for the calculator utility functions."""
    
    def test_add(self):
        """Test the add function."""
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(0, 0), 0)
        self.assertEqual(add(1.5, 2.5), 4.0)
    
    def test_subtract(self):
        """Test the subtract function."""
        self.assertEqual(subtract(5, 3), 2)
        self.assertEqual(subtract(1, 1), 0)
        self.assertEqual(subtract(0, 5), -5)
        self.assertEqual(subtract(10.5, 5.5), 5.0)
    
    def test_multiply(self):
        """Test the multiply function."""
        self.assertEqual(multiply(2, 3), 6)
        self.assertEqual(multiply(-2, 3), -6)
        self.assertEqual(multiply(0, 5), 0)
        self.assertEqual(multiply(2.5, 2), 5.0)
    
    def test_divide(self):
        """Test the divide function."""
        self.assertEqual(divide(6, 3), 2)
        self.assertEqual(divide(5, 2), 2.5)
        self.assertEqual(divide(0, 5), 0)
        self.assertEqual(divide(-6, 2), -3)
        
        # Test division by zero
        with self.assertRaises(ZeroDivisionError):
            divide(5, 0)
    
    def test_format_result(self):
        """Test the result formatting function."""
        self.assertEqual(format_result(5), "5")
        self.assertEqual(format_result(5.0), "5")
        self.assertEqual(format_result(5.123), "5.123")
        self.assertEqual(format_result(5.123000), "5.123")


class TestCalculatorMain(unittest.TestCase):
    """Test cases for the calculator main functionality."""
    
    def test_parse_input_valid(self):
        """Test the parse_input function with valid input."""
        self.assertEqual(parse_input("5 + 3"), (5.0, "+", 3.0))
        self.assertEqual(parse_input("10 - 4"), (10.0, "-", 4.0))
        self.assertEqual(parse_input("2 * 6"), (2.0, "*", 6.0))
        self.assertEqual(parse_input("8 / 2"), (8.0, "/", 2.0))
    
    def test_parse_input_invalid(self):
        """Test the parse_input function with invalid input."""
        with self.assertRaises(ValueError):
            parse_input("5 & 3")  # Invalid operator
        
        with self.assertRaises(ValueError):
            parse_input("five + 3")  # Non-numeric operand
    
    def test_calculate(self):
        """Test the calculate function."""
        # Test each operation
        self.assertEqual(calculate(5.0, "+", 3.0), 8.0)
        self.assertEqual(calculate(10.0, "-", 4.0), 6.0)
        self.assertEqual(calculate(2.0, "*", 6.0), 12.0)
        self.assertEqual(calculate(8.0, "/", 2.0), 4.0)
        
        # Test division by zero
        with self.assertRaises(ZeroDivisionError):
            calculate(5.0, "/", 0.0)
        
        # Test invalid operator
        with self.assertRaises(ValueError):
            calculate(5.0, "&", 3.0)
    
    def test_calculator_loop(self):
        """Test the calculator loop."""
        # Test with valid input and then quit
        with patch('builtins.input', side_effect=["5 + 3", "quit"]):
            with redirect_stdout(io.StringIO()) as output:
                calculator_loop()
                self.assertIn("Result: 8", output.getvalue())
        
        # Test with invalid input and then quit
        with patch('builtins.input', side_effect=["5 & 3", "quit"]):
            with redirect_stdout(io.StringIO()) as output:
                calculator_loop()
                self.assertIn("Error: Unsupported operator", output.getvalue())
        
        # Test with division by zero and then quit
        with patch('builtins.input', side_effect=["5 / 0", "quit"]):
            with redirect_stdout(io.StringIO()) as output:
                calculator_loop()
                self.assertIn("Error: Division by zero", output.getvalue())
    
    def test_main_function_interactive(self):
        """Test the main function in interactive mode."""
        # Test with interactive mode
        with patch('builtins.input', side_effect=["5 + 3", "quit"]):
            with redirect_stdout(io.StringIO()) as output:
                with patch('sys.argv', ['calculator.py']):
                    main.main()
                    self.assertIn("Result: 8", output.getvalue())
    
    def test_main_function_expression(self):
        """Test the main function with expression argument."""
        # Test with expression argument (requires modifying sys.argv)
        # This will test command-line argument handling
        with patch('sys.argv', ['calculator.py', '--expression', '10 * 5']):
            with redirect_stdout(io.StringIO()) as output:
                main.main()
                self.assertIn("Result: 50", output.getvalue())
        
        # Test with invalid expression
        with patch('sys.argv', ['calculator.py', '--expression', 'invalid']):
            with redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit):
                    main.main()
                self.assertIn("Error", output.getvalue())


# Add standalone pytest test functions
if PYTEST_AVAILABLE:
    # Standalone test functions for pytest
    def test_add_function():
        """Test the add function for pytest."""
        assert add(2, 3) == 5
        assert add(-1, 1) == 0
        assert add(0, 0) == 0
        assert add(1.5, 2.5) == 4.0
    
    def test_subtract_function():
        """Test the subtract function for pytest."""
        assert subtract(5, 3) == 2
        assert subtract(1, 1) == 0
        assert subtract(0, 5) == -5
        assert subtract(10.5, 5.5) == 5.0
    
    def test_multiply_function():
        """Test the multiply function for pytest."""
        assert multiply(2, 3) == 6
        assert multiply(-2, 3) == -6
        assert multiply(0, 5) == 0
        assert multiply(2.5, 2) == 5.0
    
    def test_divide_function():
        """Test the divide function for pytest."""
        assert divide(6, 3) == 2
        assert divide(5, 2) == 2.5
        assert divide(0, 5) == 0
        assert divide(-6, 2) == -3
        
        # Test division by zero
        with pytest.raises(ZeroDivisionError):
            divide(5, 0)
    
    def test_format_result_function():
        """Test the result formatting function for pytest."""
        assert format_result(5) == "5"
        assert format_result(5.0) == "5"
        assert format_result(5.123) == "5.123"
        assert format_result(5.123000) == "5.123"
    
    def test_parse_input_valid_function():
        """Test the parse_input function with valid input for pytest."""
        assert parse_input("5 + 3") == (5.0, "+", 3.0)
        assert parse_input("10 - 4") == (10.0, "-", 4.0)
        assert parse_input("2 * 6") == (2.0, "*", 6.0)
        assert parse_input("8 / 2") == (8.0, "/", 2.0)
    
    def test_parse_input_invalid_function():
        """Test the parse_input function with invalid input for pytest."""
        with pytest.raises(ValueError):
            parse_input("5 & 3")  # Invalid operator
        
        with pytest.raises(ValueError):
            parse_input("five + 3")  # Non-numeric operand
    
    def test_calculate_function():
        """Test the calculate function for pytest."""
        # Test each operation
        assert calculate(5.0, "+", 3.0) == 8.0
        assert calculate(10.0, "-", 4.0) == 6.0
        assert calculate(2.0, "*", 6.0) == 12.0
        assert calculate(8.0, "/", 2.0) == 4.0
        
        # Test division by zero
        with pytest.raises(ZeroDivisionError):
            calculate(5.0, "/", 0.0)
        
        # Test invalid operator
        with pytest.raises(ValueError):
            calculate(5.0, "&", 3.0)
    
    def test_calculator_loop_function():
        """Test the calculator loop for pytest."""
        # Test with valid input and then quit
        with patch('builtins.input', side_effect=["5 + 3", "quit"]):
            with redirect_stdout(io.StringIO()) as output:
                calculator_loop()
                assert "Result: 8" in output.getvalue()

    def test_main_function_interactive_pytest():
        """Test the main function in interactive mode."""
        # Test with interactive mode
        with patch('builtins.input', side_effect=["5 + 3", "quit"]):
            with redirect_stdout(io.StringIO()) as output:
                with patch('sys.argv', ['calculator.py']):
                    assert main.main() == 0
                    assert "Result: 8" in output.getvalue()
    
    def test_main_function_expression_pytest():
        """Test the main function with expression argument."""
        # Test with expression argument (requires modifying sys.argv)
        with patch('sys.argv', ['calculator.py', '--expression', '10 * 5']):
            with redirect_stdout(io.StringIO()) as output:
                assert main.main() == 0
                assert "Result: 50" in output.getvalue()


if __name__ == "__main__":
    unittest.main()
