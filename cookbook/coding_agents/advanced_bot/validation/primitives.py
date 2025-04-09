"""
Validation Primitives

This module provides core validation primitives that can be used across
different validation agents and workflows.
"""

import os
import subprocess
import importlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable

class ValidationResult:
    """
    Represents the result of a validation operation.
    
    This class provides a standardized way to represent validation results
    across different validation types and tools.
    """
    
    def __init__(
        self,
        validation_type: str,
        status: str,
        success: bool,
        details: Dict[str, Any] = None,
        issues: List[Dict[str, Any]] = None
    ):
        """
        Initialize a validation result.
        
        Args:
            validation_type: Type of validation performed
            status: Status of the validation (completed, error, skipped)
            success: Whether the validation was successful
            details: Additional details about the validation
            issues: List of issues found during validation
        """
        self.validation_type = validation_type
        self.status = status
        self.success = success
        self.details = details or {}
        self.issues = issues or []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "validation_type": self.validation_type,
            "status": self.status,
            "success": self.success,
            "details": self.details,
            "issues": self.issues
        }
    
    def add_issue(
        self,
        message: str,
        severity: str = "warning",
        location: str = None,
        code: str = None
    ) -> None:
        """
        Add an issue to the validation result.
        
        Args:
            message: Description of the issue
            severity: Severity level (error, warning, info)
            location: Where the issue was found (file, line, etc.)
            code: Code reference for the issue
        """
        self.issues.append({
            "message": message,
            "severity": severity,
            "location": location,
            "code": code
        })
        
        # Update success based on issues
        if severity == "error":
            self.success = False
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ValidationResult':
        """Create a ValidationResult from a dictionary."""
        return ValidationResult(
            validation_type=data.get("validation_type", "unknown"),
            status=data.get("status", "unknown"),
            success=data.get("success", False),
            details=data.get("details", {}),
            issues=data.get("issues", [])
        )

class ValidationRegistry:
    """
    Registry for validation primitives and tools.
    
    This class provides a central registry for validation primitives
    that can be used across different validation agents and workflows.
    """
    
    def __init__(self):
        """Initialize the validation registry."""
        self.validators: Dict[str, Callable] = {}
        
    def register(
        self,
        name: str,
        validator: Callable,
        description: str = None,
        validation_type: str = None
    ) -> None:
        """
        Register a validation primitive.
        
        Args:
            name: Name of the validator
            validator: Validator function
            description: Description of the validator
            validation_type: Type of validation performed
        """
        self.validators[name] = {
            "validator": validator,
            "description": description,
            "validation_type": validation_type
        }
        
    def get_validator(self, name: str) -> Optional[Callable]:
        """Get a validator by name."""
        validator_info = self.validators.get(name)
        if validator_info:
            return validator_info["validator"]
        return None
    
    def list_validators(self, validation_type: str = None) -> List[str]:
        """
        List available validators.
        
        Args:
            validation_type: Filter by validation type
            
        Returns:
            List of validator names
        """
        if validation_type:
            return [
                name for name, info in self.validators.items()
                if info.get("validation_type") == validation_type
            ]
        return list(self.validators.keys())
    
    def execute_validation(
        self,
        name: str,
        **kwargs
    ) -> ValidationResult:
        """
        Execute a validation primitive.
        
        Args:
            name: Name of the validator to execute
            **kwargs: Arguments to pass to the validator
            
        Returns:
            ValidationResult from the validation
        """
        validator_info = self.validators.get(name)
        if not validator_info:
            return ValidationResult(
                validation_type="unknown",
                status="error",
                success=False,
                details={"error": f"Validator '{name}' not found"}
            )
        
        try:
            validator = validator_info["validator"]
            result = validator(**kwargs)
            
            # If the result is already a ValidationResult, return it
            if isinstance(result, ValidationResult):
                return result
            
            # Otherwise, wrap it in a ValidationResult
            return ValidationResult(
                validation_type=validator_info.get("validation_type", "unknown"),
                status="completed",
                success=True,
                details=result
            )
        except Exception as e:
            return ValidationResult(
                validation_type=validator_info.get("validation_type", "unknown"),
                status="error",
                success=False,
                details={"error": str(e)}
            )

# Create a global registry instance
registry = ValidationRegistry()

# Define some basic validation primitives

def run_pytest(
    directory: str,
    pattern: str = "test_*.py",
    verbose: bool = True
) -> ValidationResult:
    """
    Run pytest on the specified directory.
    
    Args:
        directory: Directory containing the tests
        pattern: Pattern to match test files
        verbose: Whether to run in verbose mode
        
    Returns:
        ValidationResult with test results
    """
    cmd = ["pytest", directory, "-v" if verbose else ""]
    
    if pattern:
        cmd.extend(["-k", pattern])
        
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    success = result.returncode == 0
    details = {
        "output": result.stdout,
        "errors": result.stderr
    }
    
    validation_result = ValidationResult(
        validation_type="pytest",
        status="completed",
        success=success,
        details=details
    )
    
    # Parse output to find issues
    if not success:
        lines = result.stdout.split("\n")
        for line in lines:
            if "FAILED" in line:
                # Extract file and line number from failure
                parts = line.split()
                location = None
                for part in parts:
                    if ".py" in part:
                        location = part
                        break
                
                validation_result.add_issue(
                    message=line,
                    severity="error",
                    location=location
                )
    
    return validation_result

def run_flake8(
    file_path: str
) -> ValidationResult:
    """
    Run flake8 on the specified file.
    
    Args:
        file_path: Path to the file to lint
        
    Returns:
        ValidationResult with linting results
    """
    cmd = ["flake8", file_path]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    success = result.returncode == 0
    details = {
        "output": result.stdout
    }
    
    validation_result = ValidationResult(
        validation_type="flake8",
        status="completed",
        success=success,
        details=details
    )
    
    # Parse output to find issues
    lines = result.stdout.split("\n")
    for line in lines:
        if line.strip():
            parts = line.split(":", 3)
            if len(parts) >= 3:
                file_name = parts[0]
                line_number = parts[1]
                message = parts[2:]
                
                validation_result.add_issue(
                    message=" ".join(message).strip(),
                    severity="warning",
                    location=f"{file_name}:{line_number}"
                )
    
    return validation_result

def run_mypy(
    file_path: str
) -> ValidationResult:
    """
    Run mypy on the specified file.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        ValidationResult with type checking results
    """
    cmd = ["mypy", file_path]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    success = result.returncode == 0
    details = {
        "output": result.stdout
    }
    
    validation_result = ValidationResult(
        validation_type="mypy",
        status="completed",
        success=success,
        details=details
    )
    
    # Parse output to find issues
    lines = result.stdout.split("\n")
    for line in lines:
        if line.strip() and "error:" in line:
            parts = line.split(":", 3)
            if len(parts) >= 3:
                file_name = parts[0]
                line_number = parts[1]
                message = parts[2:]
                
                validation_result.add_issue(
                    message=" ".join(message).strip(),
                    severity="error",
                    location=f"{file_name}:{line_number}"
                )
    
    return validation_result

# Register the validation primitives
registry.register(
    name="run_pytest",
    validator=run_pytest,
    description="Run pytest on a directory",
    validation_type="testing"
)

registry.register(
    name="run_flake8",
    validator=run_flake8,
    description="Run flake8 linting on a file",
    validation_type="linting"
)

registry.register(
    name="run_mypy",
    validator=run_mypy,
    description="Run mypy type checking on a file",
    validation_type="type_checking"
)

# Example usage
if __name__ == "__main__":
    # Example usage of validation primitives
    print("Available validators:", registry.list_validators())
    print("Testing validators:", registry.list_validators(validation_type="testing"))
    print("Linting validators:", registry.list_validators(validation_type="linting"))
