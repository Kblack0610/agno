"""
Run Tests for Advanced Validation Bot

This script runs the tests for the advanced validation bot.
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path to import the modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import the test runner
from tests.test_runner import TestComponentsWithValidation

def run_tests():
    """Run the tests with validation steps."""
    print("=" * 80)
    print("RUNNING TESTS FOR ADVANCED VALIDATION BOT")
    print("=" * 80)
    
    # Create a test suite with our tests
    suite = unittest.TestSuite()
    
    # Add tests in order
    suite.addTest(TestComponentsWithValidation('test_01_coder_bot_code_generation'))
    suite.addTest(TestComponentsWithValidation('test_02_coder_bot_test_creation'))
    suite.addTest(TestComponentsWithValidation('test_03_validation_primitives'))
    suite.addTest(TestComponentsWithValidation('test_04_sequential_orchestrator'))
    suite.addTest(TestComponentsWithValidation('test_05_end_to_end_workflow'))
    suite.addTest(TestComponentsWithValidation('test_06_summary'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print(f"TEST RESULTS: {result.testsRun} tests run")
    print(f"Successes: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 80)
    
    return result

if __name__ == "__main__":
    run_tests()
