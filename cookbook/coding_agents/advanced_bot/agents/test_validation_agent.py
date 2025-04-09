"""
Test Validation Agent

This agent specializes in validating tests across different testing frameworks
and providing comprehensive test analysis.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Remove direct agno imports
# from agno.agent import Agent
# from agno.models.openai import OpenAIChat

# Update to absolute imports
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile

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
            model_id: str = None,
            show_tool_calls: bool = True,
            config_path: Optional[Union[str, Path]] = None
        ):
        """
        Initialize the test validation agent.
        
        Args:
            model_id: Model ID to use for analysis (overrides configuration)
            show_tool_calls: Whether to show tool calls in output
            config_path: Path to configuration file or directory
        """
        # Initialize configuration
        self.config = ConfigManager(config_path)
        
        # Initialize tools
        self.tools = TestTools()
        
        # Initialize validation profile
        profile_name = self.config.get("validation.profile", "standard")
        self.validation_profile = ValidationProfile(profile_name, self.config)
        
        # Get model ID from config if not provided
        self.model_id = model_id or self.config.get("model.id", "gpt-4o")
        self.show_tool_calls = show_tool_calls
    
    def run_tests(self, directory: str) -> Dict[str, Any]:
        """
        Run tests for the given directory.
        
        Args:
            directory: Directory to run tests for
            
        Returns:
            Dictionary with test results
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Running tests for directory: {directory}")
        
        # Use the tools to run tests
        try:
            # Run tests using pytest by default
            result = self.tools.run_pytest(
                directory=directory,
                verbose=True,
                coverage=True
            )
            
            # Analyze test results
            coverage = result.get("coverage", 0)
            threshold = self.validation_profile.get("test_coverage_threshold")
            
            return {
                "status": "completed",
                "success": coverage >= threshold,
                "details": {
                    "coverage": coverage,
                    "threshold": threshold,
                    "passed": result.get("passed", 0),
                    "failed": result.get("failed", 0),
                    "skipped": result.get("skipped", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return {
                "status": "error",
                "success": False,
                "error": str(e)
            }
    
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
        if test_type == "pytest":
            result = self.tools.run_pytest(
                directory=directory,
                verbose=True,
                coverage=coverage
            )
        else:
            result = {
                "status": "error",
                "error": f"Test type '{test_type}' not supported"
            }
        
        return result
    
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
        # For now, just run tests for the file
        return self.tools.run_pytest(
            directory=str(Path(file_path).parent),
            pattern=str(Path(file_path).name),
            verbose=True,
            coverage=True
        )

# Example usage
if __name__ == "__main__":
    agent = TestValidationAgent()
    
    # Example directory with tests
    test_dir = "examples"
    
    # Validate tests
    # In a real scenario, you would specify an actual test directory
    print(f"This is a placeholder. In a real scenario, you would use:")
    print(f"agent.validate_tests('{test_dir}')")
