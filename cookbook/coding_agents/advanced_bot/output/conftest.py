"""
Pytest configuration file for the calculator tests.

This file contains fixtures and configuration for pytest
to ensure compatibility with the validation system.
"""

import os
import sys
import pytest

# Make sure the current directory is in the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the utility functions to make them available for tests
try:
    from test_main import add, subtract, multiply, divide, format_result
    import main
except ImportError as e:
    print(f"Warning: Could not import from test_main or main: {e}")


@pytest.fixture
def calculator_utils():
    """Fixture providing calculator utility functions."""
    return {
        "add": add,
        "subtract": subtract,
        "multiply": multiply,
        "divide": divide,
        "format_result": format_result
    }


@pytest.fixture
def calculator_main():
    """Fixture providing the main calculator module."""
    return main


def pytest_configure(config):
    """Configure pytest with markers for our tests."""
    config.addinivalue_line("markers", "utils: tests for utility functions")
    config.addinivalue_line("markers", "main: tests for main functionality")
