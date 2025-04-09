"""
Mock Coder Bot for testing purposes

This provides a simplified version of the CoderBot class for testing
"""

import os
import json
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

class CoderBot:
    """Mock version of the CoderBot agent for testing purposes"""
    
    def __init__(
            self,
            model_id: str = "gpt-4o",
            work_dir: str = None,
            storage_dir: str = None,
            show_tool_calls: bool = True
        ):
        """
        Initialize the coder bot.
        
        Args:
            model_id: Model ID to use for coding
            work_dir: Working directory for the bot
            storage_dir: Directory for storage and knowledge bases
            show_tool_calls: Whether to show tool calls in output
        """
        self.work_dir = work_dir or os.getcwd()
        self.storage_dir = storage_dir or os.path.join(self.work_dir, '.coding_bot')
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def generate_code(
            self,
            description: str,
            language: str = "python",
            file_path: str = None
        ) -> Dict[str, Any]:
        """
        Generate code based on a description.
        
        Args:
            description: Description of the code to generate
            language: Programming language
            file_path: Path to save the generated code
            
        Returns:
            Dictionary with generated code
        """
        # For testing purposes, generate a simple function
        if 'fibonacci' in description.lower():
            code = '''
def calculate_fibonacci(n):
    """
    Calculate Fibonacci sequence up to n terms.
    
    Args:
        n: Number of terms to generate
        
    Returns:
        List of Fibonacci numbers
    """
    fibonacci = [0, 1]
    
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    for i in range(2, n):
        fibonacci.append(fibonacci[i-1] + fibonacci[i-2])
    
    return fibonacci
'''
        else:
            code = f'''
def generated_function():
    """
    Function generated based on description: {description}
    """
    # Implementation would go here
    pass
'''
        
        # Save the code to a file if specified
        if file_path:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, 'w') as f:
                f.write(code)
        
        return {
            "code": code,
            "language": language,
            "file_path": file_path
        }
    
    def modify_code(
            self,
            file_path: str,
            modification_description: str
        ) -> Dict[str, Any]:
        """
        Modify existing code based on a description.
        
        Args:
            file_path: Path to the file to modify
            modification_description: Description of the modifications to make
            
        Returns:
            Dictionary with modification results
        """
        # Read the original file
        with open(file_path, 'r') as f:
            original_code = f.read()
        
        # For testing purposes, implement specific fixes
        if 'multiply' in modification_description and 'divide' in modification_description:
            # Fix the calculator example
            modified_code = original_code.replace(
                'return a + b',
                'return a * b'
            ).replace(
                'return a / b',
                """if b == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return a / b"""
            )
        else:
            # Generic modification
            modified_code = original_code + '\n# Modified based on: ' + modification_description
        
        # Save the modified code
        with open(file_path, 'w') as f:
            f.write(modified_code)
        
        return {
            "original_code": original_code,
            "modified_code": modified_code,
            "file_path": file_path,
            "modifications": [modification_description]
        }
    
    def create_tests(
            self,
            file_path: str,
            test_framework: str = "pytest"
        ) -> Dict[str, Any]:
        """
        Create tests for the code in the specified file.
        
        Args:
            file_path: Path to the file to test
            test_framework: Testing framework to use
            
        Returns:
            Dictionary with test creation results
        """
        # Read the source file
        with open(file_path, 'r') as f:
            source_code = f.read()
        
        # Create test file path
        file_name = os.path.basename(file_path)
        test_file_name = f"test_{file_name}"
        test_file_path = os.path.join(os.path.dirname(file_path), test_file_name)
        
        # For testing purposes, generate simple tests
        if 'fibonacci' in source_code:
            test_code = '''
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
'''
        elif 'Calculator' in source_code:
            test_code = '''
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
'''
        else:
            # Generic test template
            module_name = os.path.splitext(file_name)[0]
            test_code = f'''
import pytest
from {module_name} import *

def test_example():
    """Example test."""
    assert True
'''
        
        # Save the test code
        with open(test_file_path, 'w') as f:
            f.write(test_code)
        
        return {
            "test_code": test_code,
            "test_file": test_file_path,
            "test_framework": test_framework,
            "source_file": file_path
        }
