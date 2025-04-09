
"""
Mock Validation Primitives for testing purposes

This provides simplified versions of ValidationResult and ValidationRegistry for testing
"""

import json
from typing import Dict, List, Any, Optional, Union

class ValidationResult:
    """Mock version of the ValidationResult class for testing purposes"""
    
    def __init__(
            self,
            validation_type: str,
            status: str,
            success: bool,
            details: Dict[str, Any] = None,
            issues: List[Dict[str, Any]] = None
        ):
        """
        Initialize the validation result.
        
        Args:
            validation_type: Type of validation
            status: Status of the validation
            success: Whether the validation was successful
            details: Details about the validation
            issues: Issues found during validation
        """
        self.validation_type = validation_type
        self.status = status
        self.success = success
        self.details = details or {}
        self.issues = issues or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the validation result to a dictionary."""
        return {
            "validation_type": self.validation_type,
            "status": self.status,
            "success": self.success,
            "details": self.details,
            "issues": self.issues
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        """Create a validation result from a dictionary."""
        return cls(
            validation_type=data["validation_type"],
            status=data["status"],
            success=data["success"],
            details=data.get("details", {}),
            issues=data.get("issues", [])
        )

class ValidationRegistry:
    """Mock version of the ValidationRegistry class for testing purposes"""
    
    def __init__(self):
        """Initialize the validation registry."""
        self.validators = {}
    
    def register(self, name: str, validator_fn: callable):
        """Register a validator function."""
        self.validators[name] = validator_fn
    
    def validate(self, name: str, **kwargs) -> ValidationResult:
        """Run a validator by name."""
        if name not in self.validators:
            return ValidationResult(
                validation_type=name,
                status="error",
                success=False,
                details={"error": f"Validator '{name}' not found"}
            )
        
        try:
            return self.validators[name](**kwargs)
        except Exception as e:
            return ValidationResult(
                validation_type=name,
                status="error",
                success=False,
                details={"error": str(e)}
            )
