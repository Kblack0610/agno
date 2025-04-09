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
import logging

# Remove direct agno imports
# from agno.agent import Agent
# from agno.models.openai import OpenAIChat

# Update to absolute imports
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile

# Import new test generator and Claude API
try:
    from utils.test_generator import TestGenerator, CodeAnalyzer
    TEST_GENERATOR_AVAILABLE = True
except ImportError:
    TEST_GENERATOR_AVAILABLE = False
    
try:
    from utils.claude_api import ClaudeAPI
    CLAUDE_API_AVAILABLE = True
except ImportError:
    CLAUDE_API_AVAILABLE = False

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
    It can also generate tests for Python code using templates or Claude 3.7 API.
    """
    
    def __init__(
            self,
            model_id: str = None,
            show_tool_calls: bool = True,
            config_path: Optional[Union[str, Path]] = None,
            verbose: bool = False,
            use_claude: bool = True,
            claude_api_key: Optional[str] = None
        ):
        """
        Initialize the test validation agent.
        
        Args:
            model_id: Model ID to use for analysis (overrides configuration)
            show_tool_calls: Whether to show tool calls in output
            config_path: Path to configuration file or directory
            verbose: Whether to enable verbose logging
            use_claude: Whether to use Claude API for test generation
            claude_api_key: API key for Claude (optional if set in env var)
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
        self.verbose = verbose
        
        # Set up logging
        self.logger = logging.getLogger('agent.TestValidationAgent')
        log_level = logging.DEBUG if verbose else logging.INFO
        self.logger.setLevel(log_level)
        
        # Initialize test generator if available
        self.test_generator = None
        if TEST_GENERATOR_AVAILABLE:
            use_claude_for_generator = use_claude and CLAUDE_API_AVAILABLE
            self.test_generator = TestGenerator(use_claude=use_claude_for_generator, claude_api_key=claude_api_key)
            if self.verbose:
                self.logger.info(f"Test generator initialized (using Claude: {use_claude_for_generator})")
        elif self.verbose:
            self.logger.warning("Test generator not available. Some functionality will be limited.")
        
        # Initialize Claude API if available and requested
        self.claude_api = None
        if use_claude and CLAUDE_API_AVAILABLE:
            try:
                self.claude_api = ClaudeAPI(api_key=claude_api_key)
                if self.verbose:
                    self.logger.info("Claude API initialized for improved reasoning")
            except Exception as e:
                self.logger.error(f"Failed to initialize Claude API: {e}")
        
        self.logger.info("TestValidationAgent initialized")
    
    def run_tests(self, directory: str) -> Dict[str, Any]:
        """
        Run tests for the given directory.
        
        Args:
            directory: Directory to run tests for
            
        Returns:
            Dictionary with test results
        """
        self.logger.info(f"Running tests for directory: {directory}")
        
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
            self.logger.error(f"Error running tests: {e}")
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
    
    def generate_tests(
            self,
            file_path: str,
            output_path: Optional[str] = None,
            test_framework: str = "pytest",
            use_claude: Optional[bool] = None
        ) -> Dict[str, Any]:
        """
        Generate tests for a given Python file.
        
        Args:
            file_path: Path to the Python file to generate tests for
            output_path: Path to write the generated tests (defaults to test_<filename>.py)
            test_framework: Test framework to use (pytest, unittest)
            use_claude: Whether to use Claude API for test generation, overrides instance setting
            
        Returns:
            Dictionary with generation results
        """
        if not TEST_GENERATOR_AVAILABLE:
            error_msg = "Test generator not available. Please install the required dependencies."
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        self.logger.info(f"Generating tests for file: {file_path}")
        
        # Determine whether to use Claude
        should_use_claude = use_claude if use_claude is not None else (self.claude_api is not None)
        
        # If generator was initialized without Claude but we want to use it now
        if should_use_claude and not self.test_generator.use_claude and self.claude_api:
            self.test_generator.use_claude = True
            self.test_generator.claude_api = self.claude_api
        
        # Generate tests
        try:
            result = self.test_generator.generate_tests(
                file_path=file_path,
                output_path=output_path,
                test_framework=test_framework
            )
            
            if self.verbose:
                if result["success"]:
                    self.logger.info(f"Successfully generated tests at {result['test_file']}")
                else:
                    self.logger.error(f"Failed to generate tests: {result.get('error', 'Unknown error')}")
            
            return result
        
        except Exception as e:
            error_msg = f"Error generating tests: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def generate_tests_for_directory(
            self,
            directory: str,
            output_dir: Optional[str] = None,
            test_framework: str = "pytest",
            pattern: str = "*.py",
            exclude_patterns: List[str] = None,
            include_subdirs: bool = True
        ) -> Dict[str, Any]:
        """
        Generate tests for all Python files in a directory.
        
        Args:
            directory: Directory containing Python files
            output_dir: Directory to write generated tests
            test_framework: Test framework to use
            pattern: Pattern to match Python files
            exclude_patterns: Patterns to exclude
            include_subdirs: Whether to include subdirectories
            
        Returns:
            Dictionary with generation results
        """
        if not TEST_GENERATOR_AVAILABLE:
            error_msg = "Test generator not available. Please install the required dependencies."
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        self.logger.info(f"Generating tests for directory: {directory}")
        
        # Find Python files
        directory_path = Path(directory)
        if not directory_path.exists() or not directory_path.is_dir():
            error_msg = f"Directory not found: {directory}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Set up output directory
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = None
        
        # Initialize exclude patterns
        if exclude_patterns is None:
            exclude_patterns = ["*test_*.py", "*/tests/*", "*/test/*"]
        
        # Find Python files
        python_files = []
        glob_pattern = "**/*.py" if include_subdirs else "*.py"
        
        for file_path in directory_path.glob(glob_pattern):
            # Check if file matches pattern and is not excluded
            if not self._matches_pattern(file_path.name, pattern):
                continue
                
            should_exclude = any(self._matches_pattern(str(file_path), ex_pattern) for ex_pattern in exclude_patterns)
            if should_exclude:
                continue
                
            python_files.append(file_path)
        
        if not python_files:
            self.logger.warning(f"No Python files found in {directory} matching pattern {pattern}")
            return {"success": True, "files_processed": 0, "results": []}
        
        # Generate tests for each file
        results = []
        success_count = 0
        
        for file_path in python_files:
            # Determine output path for this file
            file_output_path = None
            if output_path:
                rel_path = file_path.relative_to(directory_path)
                test_filename = f"test_{file_path.name}"
                file_output_path = output_path / rel_path.parent / test_filename
            
            # Generate tests
            result = self.generate_tests(
                file_path=str(file_path),
                output_path=str(file_output_path) if file_output_path else None,
                test_framework=test_framework
            )
            
            results.append({
                "source_file": str(file_path),
                "success": result["success"],
                "test_file": result.get("test_file"),
                "error": result.get("error")
            })
            
            if result["success"]:
                success_count += 1
        
        return {
            "success": True,
            "files_processed": len(python_files),
            "successful_generations": success_count,
            "failed_generations": len(python_files) - success_count,
            "results": results
        }
    
    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if a filename matches a glob pattern."""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)

# Example usage
if __name__ == "__main__":
    agent = TestValidationAgent(verbose=True)
    
    # Example directory with tests
    test_dir = "examples"
    
    # Validate tests
    # In a real scenario, you would specify an actual test directory
    print(f"This is a placeholder. In a real scenario, you would use:")
    print(f"agent.validate_tests('{test_dir}')")
    print(f"agent.generate_tests('path/to/python_file.py')")
