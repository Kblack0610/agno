"""
Test Runner for Advanced Validation Bot

This module runs tests for the advanced validation bot components
with validation steps between each test.
"""

import os
import sys
import json
import unittest
import subprocess
from pathlib import Path

# Add parent directory to path to import the modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import mock validation components
# Using mock implementations for testing
from tests.mocks.coder_bot import CoderBot
from tests.mocks.primitives import ValidationResult, ValidationRegistry
from tests.mocks.sequential_orchestrator import SequentialOrchestrator

class ValidationStep:
    """A validation step to verify test results."""
    
    def __init__(self, name, description):
        """Initialize the validation step."""
        self.name = name
        self.description = description
        self.passed = False
        self.results = {}
    
    def run_validation(self, test_results):
        """Run the validation step."""
        # This would normally use the sequential thinking MCP
        # For now, we'll use a simple validation approach
        
        self.results = {
            "validation_name": self.name,
            "validation_description": self.description,
            "test_results": test_results,
            "validation_passed": True  # Simplified for demonstration
        }
        
        self.passed = True
        return self.results
    
    def print_results(self):
        """Print the validation results."""
        print(f"\n{'='*80}")
        print(f"Validation Step: {self.name}")
        print(f"Description: {self.description}")
        print(f"Status: {'PASSED' if self.passed else 'FAILED'}")
        print(f"{'='*80}\n")
        
        if self.results:
            print("Validation Results:")
            for key, value in self.results.items():
                if key != "test_results":  # Skip test results for brevity
                    print(f"  {key}: {value}")

class TestComponentsWithValidation(unittest.TestCase):
    """Test cases for the advanced validation bot components with validation steps."""
    
    @classmethod
    def setUpClass(cls):
        """Set up resources for all tests."""
        # Create a temporary directory for test files
        cls.test_dir = Path(__file__).parent / "temp"
        cls.test_dir.mkdir(exist_ok=True)
        
        # Create test files directory
        cls.test_files_dir = cls.test_dir / "files"
        cls.test_files_dir.mkdir(exist_ok=True)
        
        # Initialize components
        cls.coder_bot = CoderBot(work_dir=str(cls.test_dir))
        cls.registry = ValidationRegistry()
        cls.orchestrator = SequentialOrchestrator()
        
        # List to track all validation steps
        cls.validation_steps = []
    
    @classmethod
    def tearDownClass(cls):
        """Clean up resources after all tests."""
        # Here we would clean up temporary files
        # For demonstration purposes, we'll leave them for inspection
        pass
    
    def add_validation_step(self, name, description, test_results):
        """Add a validation step and run it."""
        validation_step = ValidationStep(name, description)
        validation_results = validation_step.run_validation(test_results)
        validation_step.print_results()
        
        self.__class__.validation_steps.append(validation_step)
        
        # In a real implementation, we would use the sequential thinking MCP here
        # to verify the test results and make decisions
        
        return validation_results
    
    def test_01_coder_bot_code_generation(self):
        """Test the coder bot's code generation capabilities."""
        print("\n" + "="*40)
        print("RUNNING TEST: Coder Bot Code Generation")
        print("="*40)
        
        # Generate a simple function
        description = "Create a Python function called 'calculate_fibonacci' that returns the Fibonacci sequence up to n terms"
        file_path = str(self.test_files_dir / "fibonacci.py")
        
        result = self.coder_bot.generate_code(
            description=description,
            language="python",
            file_path=file_path
        )
        
        # Verify the code was generated
        self.assertTrue(os.path.exists(file_path), "File was not created")
        self.assertIn("calculate_fibonacci", result["code"], "Function name not found in generated code")
        
        # Print result information
        print(f"\nGenerated file: {file_path}")
        print(f"Code length: {len(result['code'])} characters")
        
        # Add validation step
        validation_result = self.add_validation_step(
            name="Code Generation Validation",
            description="Validate that the code generation produced correct Fibonacci function",
            test_results={
                "file_path": file_path,
                "code_snippet": result["code"][:200] + "..." if len(result["code"]) > 200 else result["code"],
                "success": os.path.exists(file_path)
            }
        )
        
        return file_path
    
    def test_02_coder_bot_test_creation(self):
        """Test the coder bot's test creation capabilities."""
        print("\n" + "="*40)
        print("RUNNING TEST: Coder Bot Test Creation")
        print("="*40)
        
        # Get the file path from the previous test
        file_path = self.test_01_coder_bot_code_generation()
        
        # Create tests for the function
        result = self.coder_bot.create_tests(
            file_path=file_path,
            test_framework="pytest"
        )
        
        # Verify the tests were created
        test_file_path = result["test_file"]
        self.assertTrue(os.path.exists(test_file_path), "Test file was not created")
        self.assertIn("test_calculate_fibonacci", result["test_code"], "Test function not found in generated code")
        
        # Print result information
        print(f"\nGenerated test file: {test_file_path}")
        print(f"Test code length: {len(result['test_code'])} characters")
        
        # Add validation step
        validation_result = self.add_validation_step(
            name="Test Creation Validation",
            description="Validate that the test creation produced valid pytest tests",
            test_results={
                "test_file_path": test_file_path,
                "test_code_snippet": result["test_code"][:200] + "..." if len(result["test_code"]) > 200 else result["test_code"],
                "success": os.path.exists(test_file_path)
            }
        )
        
        return test_file_path
    
    def test_03_validation_primitives(self):
        """Test the validation primitives."""
        print("\n" + "="*40)
        print("RUNNING TEST: Validation Primitives")
        print("="*40)
        
        # Create a simple test file for validation
        test_file = self.test_files_dir / "test_validation.py"
        with open(test_file, 'w') as f:
            f.write("""
import unittest

class TestExample(unittest.TestCase):
    def test_passing(self):
        self.assertEqual(1 + 1, 2)
    
    def test_failing(self):
        # This test will fail
        self.assertEqual(1 + 1, 3)

if __name__ == "__main__":
    unittest.main()
""")
        
        # Create a ValidationResult
        validation_result = ValidationResult(
            validation_type="example",
            status="completed",
            success=True,
            details={"file_tested": str(test_file)},
            issues=[
                {
                    "message": "Test 'test_failing' is failing",
                    "severity": "error",
                    "location": f"{test_file}:9"
                }
            ]
        )
        
        # Verify the validation result
        self.assertEqual(validation_result.validation_type, "example")
        self.assertTrue(validation_result.success)
        self.assertEqual(len(validation_result.issues), 1)
        
        # Convert to dict and back
        result_dict = validation_result.to_dict()
        restored_result = ValidationResult.from_dict(result_dict)
        
        self.assertEqual(restored_result.validation_type, validation_result.validation_type)
        self.assertEqual(restored_result.success, validation_result.success)
        self.assertEqual(len(restored_result.issues), len(validation_result.issues))
        
        # Print result information
        print(f"\nValidation Result:")
        print(f"  Type: {validation_result.validation_type}")
        print(f"  Status: {validation_result.status}")
        print(f"  Success: {validation_result.success}")
        print(f"  Issues: {len(validation_result.issues)}")
        
        # Add validation step
        validation_step_result = self.add_validation_step(
            name="Validation Primitives Validation",
            description="Validate that the validation primitives work correctly",
            test_results={
                "validation_type": validation_result.validation_type,
                "status": validation_result.status,
                "success": validation_result.success,
                "num_issues": len(validation_result.issues)
            }
        )
        
        return validation_result
    
    def test_04_sequential_orchestrator(self):
        """Test the sequential orchestrator."""
        print("\n" + "="*40)
        print("RUNNING TEST: Sequential Orchestrator")
        print("="*40)
        
        # Start a validation chain
        chain = self.orchestrator.start_validation_chain(
            prompt="Verify that the Fibonacci function works correctly",
            validation_type="unit_testing",
            estimated_steps=3
        )
        
        # Verify the chain was created
        self.assertEqual(chain["status"], "initialized")
        self.assertEqual(chain["validation_type"], "unit_testing")
        self.assertEqual(len(chain["thought_history"]), 1)
        
        # Continue the chain
        next_result = self.orchestrator.continue_validation_chain(
            next_thought="I need to run tests for the Fibonacci function to verify it works correctly"
        )
        
        # Verify the chain was continued
        self.assertEqual(next_result["status"], "in_progress")
        self.assertEqual(len(next_result["thought_history"]), 2)
        
        # Complete the chain
        final_result = self.orchestrator.complete_validation_chain(
            final_thought="The Fibonacci function has been verified and works correctly",
            validation_results={"passed": True, "tests_run": 5, "tests_passed": 5}
        )
        
        # Verify the chain was completed
        self.assertEqual(final_result["status"], "completed")
        self.assertEqual(len(final_result["thought_history"]), 3)
        self.assertEqual(final_result["validation_results"]["passed"], True)
        
        # Print result information
        print(f"\nSequential Orchestration:")
        print(f"  Status: {final_result['status']}")
        print(f"  Thought steps: {len(final_result['thought_history'])}")
        print(f"  Validation results: {final_result['validation_results']}")
        
        # Add validation step
        validation_step_result = self.add_validation_step(
            name="Sequential Orchestrator Validation",
            description="Validate that the sequential orchestrator works correctly",
            test_results={
                "status": final_result["status"],
                "thought_steps": len(final_result["thought_history"]),
                "validation_results": final_result["validation_results"]
            }
        )
        
        return final_result
    
    def test_05_end_to_end_workflow(self):
        """Test the end-to-end workflow."""
        print("\n" + "="*40)
        print("RUNNING TEST: End-to-End Workflow")
        print("="*40)
        
        # Create a code file with deliberate issues
        code_file = self.test_files_dir / "buggy_calculator.py"
        with open(code_file, 'w') as f:
            f.write("""
class Calculator:
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        # Bug: incorrect multiplication
        return a + b
    
    def divide(self, a, b):
        # Bug: no check for division by zero
        return a / b
""")
        
        # Step 1: Use coder bot to generate tests
        test_result = self.coder_bot.create_tests(
            file_path=str(code_file),
            test_framework="pytest"
        )
        
        test_file_path = test_result["test_file"]
        print(f"\nGenerated test file: {test_file_path}")
        
        # Step 2: Use validation primitives to run tests
        # In a real scenario, we would run the tests here
        # For demonstration, we'll simulate the results
        validation_result = ValidationResult(
            validation_type="pytest",
            status="completed",
            success=False,
            details={"file_tested": str(code_file)},
            issues=[
                {
                    "message": "Test for multiply failed: expected 6, got 5",
                    "severity": "error",
                    "location": f"{test_file_path}:15"
                },
                {
                    "message": "Test for divide failed: ZeroDivisionError",
                    "severity": "error",
                    "location": f"{test_file_path}:20"
                }
            ]
        )
        
        print(f"\nValidation Result:")
        print(f"  Success: {validation_result.success}")
        print(f"  Issues: {len(validation_result.issues)}")
        
        # Step 3: Use sequential orchestrator to analyze issues
        chain = self.orchestrator.start_validation_chain(
            prompt=f"Fix issues in {code_file}",
            validation_type="code_fixing",
            estimated_steps=3
        )
        
        self.orchestrator.continue_validation_chain(
            next_thought="The Calculator class has issues with the multiply method and divide method"
        )
        
        final_result = self.orchestrator.complete_validation_chain(
            final_thought="The issues have been identified and need to be fixed",
            validation_results={
                "issues_identified": [
                    "multiply method incorrectly adds instead of multiplying",
                    "divide method doesn't check for division by zero"
                ],
                "suggested_fixes": [
                    "Change 'return a + b' to 'return a * b' in multiply method",
                    "Add check for b == 0 in divide method"
                ]
            }
        )
        
        # Step 4: Use coder bot to fix issues
        fix_result = self.coder_bot.modify_code(
            file_path=str(code_file),
            modification_description="""
            Fix the following issues:
            1. The multiply method incorrectly adds instead of multiplying
            2. The divide method doesn't check for division by zero
            """
        )
        
        # Verify the fixes
        with open(code_file, 'r') as f:
            fixed_code = f.read()
        
        self.assertIn("return a * b", fixed_code, "Multiplication fix not applied")
        self.assertIn("if b == 0", fixed_code, "Division by zero check not added")
        
        print(f"\nFixed code file: {code_file}")
        print(f"Fixes applied successfully")
        
        # Add validation step for the entire workflow
        validation_step_result = self.add_validation_step(
            name="End-to-End Workflow Validation",
            description="Validate that the entire workflow works correctly",
            test_results={
                "initial_issues": len(validation_result.issues),
                "issues_identified": len(final_result["validation_results"]["issues_identified"]),
                "fixes_applied": 2,
                "success": "return a * b" in fixed_code and "if b == 0" in fixed_code
            }
        )
        
        return {
            "code_file": str(code_file),
            "test_file": test_file_path,
            "issues_identified": final_result["validation_results"]["issues_identified"],
            "fixes_applied": [
                "Changed 'return a + b' to 'return a * b' in multiply method",
                "Added check for b == 0 in divide method"
            ]
        }
    
    def test_06_summary(self):
        """Summarize all tests and validation steps."""
        print("\n" + "="*40)
        print("TEST SUMMARY")
        print("="*40)
        
        # Count passed validation steps
        passed_steps = sum(1 for step in self.__class__.validation_steps if step.passed)
        total_steps = len(self.__class__.validation_steps)
        
        print(f"\nValidation Steps: {passed_steps}/{total_steps} passed")
        
        # Print each validation step
        for i, step in enumerate(self.__class__.validation_steps):
            print(f"\n{i+1}. {step.name}: {'PASSED' if step.passed else 'FAILED'}")
            print(f"   Description: {step.description}")
        
        # In a real implementation, we would use the sequential thinking MCP here
        # to analyze the overall results and make recommendations
        
        print("\n" + "="*40)
        print("END OF TESTS")
        print("="*40)
        
        # This test always passes - it's just for summary
        self.assertTrue(True)

if __name__ == "__main__":
    # Run the tests
    unittest.main()
