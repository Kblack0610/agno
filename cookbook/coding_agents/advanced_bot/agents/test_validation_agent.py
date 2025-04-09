"""
Test Validation Agent

This agent specializes in validating tests across different testing frameworks
and providing comprehensive test analysis.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from agno.agent import Agent
from agno.models.openai import OpenAIChat

class TestTools:
    """Tools for test validation and execution."""
    
    def run_pytest(
        self, 
        directory: str,
        pattern: str = "test_*.py",
        verbose: bool = True,
        coverage: bool = False
    ) -> Dict[str, Any]:
        """
        Run pytest on the specified directory.
        
        Args:
            directory: Directory containing the tests
            pattern: Pattern to match test files
            verbose: Whether to run in verbose mode
            coverage: Whether to collect coverage data
            
        Returns:
            Dictionary with test results
        """
        cmd = ["pytest", directory, "-v" if verbose else ""]
        
        if pattern:
            cmd.extend(["-k", pattern])
            
        if coverage:
            cmd.extend(["--cov", directory])
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr,
            "summary": self._parse_pytest_output(result.stdout)
        }
    
    def run_unittest(
        self,
        test_module: str
    ) -> Dict[str, Any]:
        """
        Run unittest on the specified module.
        
        Args:
            test_module: Module containing the tests
            
        Returns:
            Dictionary with test results
        """
        cmd = ["python", "-m", "unittest", test_module]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    
    def get_test_coverage(
        self,
        directory: str
    ) -> Dict[str, Any]:
        """
        Get test coverage information.
        
        Args:
            directory: Directory to check coverage for
            
        Returns:
            Dictionary with coverage information
        """
        cmd = ["coverage", "run", "-m", "pytest", directory]
        subprocess.run(cmd, capture_output=True, text=True)
        
        cmd = ["coverage", "report"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "summary": self._parse_coverage_output(result.stdout)
        }
    
    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract summary information."""
        # This is a simplified parser
        lines = output.strip().split("\n")
        summary = {}
        
        for line in lines:
            if "passed" in line and "failed" in line:
                parts = line.split()
                for part in parts:
                    if "passed" in part:
                        summary["passed"] = int(part.split("passed")[0])
                    if "failed" in part:
                        summary["failed"] = int(part.split("failed")[0])
        
        return summary
    
    def _parse_coverage_output(self, output: str) -> Dict[str, Any]:
        """Parse coverage output to extract summary information."""
        # This is a simplified parser
        lines = output.strip().split("\n")
        summary = {}
        
        for line in lines:
            if "TOTAL" in line:
                parts = line.split()
                if len(parts) >= 4:
                    summary["coverage_percent"] = float(parts[-1].replace("%", ""))
        
        return summary
    
    def get_file_content(self, file_path: str) -> str:
        """Get the content of a file."""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

class TestValidationAgent:
    """
    Agent specialized in test validation and analysis.
    
    This agent runs tests, analyzes test results, and provides insights
    and recommendations for improving test coverage and quality.
    """
    
    def __init__(
        self,
        model_id: str = "gpt-4o",
        show_tool_calls: bool = True
    ):
        """
        Initialize the test validation agent.
        
        Args:
            model_id: Model ID to use for analysis
            show_tool_calls: Whether to show tool calls in output
        """
        self.tools = TestTools()
        self.agent = Agent(
            name="Test Validation Agent",
            model=OpenAIChat(id=model_id),
            description="An agent that specializes in test validation and analysis",
            instructions="""
            You are a Test Validation Agent that specializes in running tests,
            analyzing test results, and providing insights for improving test
            coverage and quality.
            
            Your responsibilities include:
            1. Running tests using different testing frameworks
            2. Analyzing test results and failures
            3. Checking test coverage and quality
            4. Providing recommendations for improving tests
            5. Identifying untested code paths and edge cases
            
            Follow these guidelines when analyzing tests:
            - Be thorough in analyzing test failures
            - Look for edge cases that might not be covered
            - Check for proper assertions and validations
            - Suggest improvements for test structure and readability
            - Recommend additional tests where coverage is lacking
            
            Format your analysis with:
            - Summary of test results (passed/failed)
            - Detailed analysis of failures
            - Coverage assessment
            - Recommendations for improvements
            - Suggested additional tests
            """,
            tools=[self.tools],
            show_tool_calls=show_tool_calls,
            markdown=True,
        )
    
    def validate_tests(
        self,
        directory: str,
        test_type: str = "pytest",
        coverage: bool = True
    ) -> Dict[str, Any]:
        """
        Run validation on tests in the specified directory.
        
        Args:
            directory: Directory containing the tests
            test_type: Type of tests (pytest, unittest)
            coverage: Whether to check coverage
            
        Returns:
            Dictionary with validation results
        """
        # Get the test files
        test_files = []
        for root, _, files in os.walk(directory):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(os.path.join(root, file))
        
        # Run the tests
        if test_type == "pytest":
            test_results = self.tools.run_pytest(directory)
        elif test_type == "unittest":
            # For unittest, we'd need to specify modules
            # This is a simplified example
            test_results = self.tools.run_unittest(directory)
        else:
            test_results = {"error": f"Unsupported test type: {test_type}"}
        
        # Get coverage if requested
        coverage_results = {}
        if coverage and test_type == "pytest":
            coverage_results = self.tools.get_test_coverage(directory)
        
        # Build a prompt for the agent to analyze the results
        prompt = f"""
        Analyze the following test results:
        
        Test Type: {test_type}
        Directory: {directory}
        
        Test Results:
        ```
        {test_results.get('output', 'No output')}
        ```
        
        Coverage Results:
        ```
        {coverage_results.get('output', 'No coverage data')}
        ```
        
        Please provide:
        1. A summary of the test results
        2. Analysis of any test failures
        3. Assessment of test coverage
        4. Recommendations for improving the tests
        """
        
        # Run the agent to analyze the results
        analysis = self.agent.run(prompt)
        
        return {
            "test_results": test_results,
            "coverage_results": coverage_results,
            "analysis": analysis
        }
    
    def analyze_test_file(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Analyze a single test file.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            Dictionary with analysis results
        """
        # Get the file content
        content = self.tools.get_file_content(file_path)
        
        # Build a prompt for the agent to analyze the file
        prompt = f"""
        Analyze the following test file:
        
        File: {file_path}
        
        ```python
        {content}
        ```
        
        Please provide:
        1. A summary of the tests in this file
        2. Analysis of test coverage and thoroughness
        3. Identification of any missing edge cases
        4. Recommendations for improving the tests
        """
        
        # Run the agent to analyze the file
        analysis = self.agent.run(prompt)
        
        return {
            "file_path": file_path,
            "content": content,
            "analysis": analysis
        }

# Example usage
if __name__ == "__main__":
    agent = TestValidationAgent()
    
    # Example directory with tests
    test_dir = "examples"
    
    # Validate tests
    # In a real scenario, you would specify an actual test directory
    print(f"This is a placeholder. In a real scenario, you would use:")
    print(f"agent.validate_tests('{test_dir}')")
