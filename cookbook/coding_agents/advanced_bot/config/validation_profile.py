"""
Validation Profile for Advanced Validation Bot.

This module defines validation profiles that control validation behavior,
setting different thresholds and rules for different validation scenarios.
"""

import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING

# Avoid circular import
if TYPE_CHECKING:
    from .config_manager import ConfigManager

# Set up logging
logger = logging.getLogger(__name__)

class ValidationProfile:
    """
    Validation profile that defines validation rules and thresholds.
    
    Available profiles:
    - strict: Strict validation with high thresholds
    - standard: Standard validation with reasonable thresholds
    - minimal: Minimal validation with low thresholds
    - custom: Custom validation with user-defined thresholds
    """
    
    # Define predefined profiles
    PROFILES = {
        "strict": {
            "test_coverage_threshold": 90,
            "complexity_threshold": 7,
            "lint_error_threshold": 0,
            "lint_warning_threshold": 5,
            "type_check_required": True,
            "fail_on_any_issue": True,
            "security_scan_required": True,
            "performance_check_required": True,
            "validation_level": "high"
        },
        "standard": {
            "test_coverage_threshold": 70,
            "complexity_threshold": 10,
            "lint_error_threshold": 0,
            "lint_warning_threshold": 10,
            "type_check_required": True,
            "fail_on_any_issue": False,
            "security_scan_required": False,
            "performance_check_required": False,
            "validation_level": "medium"
        },
        "minimal": {
            "test_coverage_threshold": 50,
            "complexity_threshold": 15,
            "lint_error_threshold": 5,
            "lint_warning_threshold": 20,
            "type_check_required": False,
            "fail_on_any_issue": False,
            "security_scan_required": False,
            "performance_check_required": False,
            "validation_level": "low"
        },
        "custom": {
            # Custom profile starts with standard values but can be overridden
            "test_coverage_threshold": 70,
            "complexity_threshold": 10,
            "lint_error_threshold": 0,
            "lint_warning_threshold": 10,
            "type_check_required": True,
            "fail_on_any_issue": False,
            "security_scan_required": False,
            "performance_check_required": False,
            "validation_level": "medium"
        }
    }
    
    def __init__(self, profile_name: str, config: 'ConfigManager'):
        """
        Initialize a validation profile.
        
        Args:
            profile_name: Name of the profile (standard, strict, minimal, custom)
            config: ConfigManager instance with configuration settings
        """
        self.name = profile_name.lower()
        self.config = config
        
        # Initialize profile thresholds
        self._profile_settings = {}
        
        # Check if the profile name is valid, otherwise fall back to standard
        if self.name not in ["standard", "strict", "minimal", "custom"]:
            logger.warning(f"Unknown profile: {self.name}, falling back to standard profile")
            self.name = "standard"
        
        # Load profile settings
        if self.name == "custom":
            self._load_custom_profile()
        else:
            self._load_predefined_profile()
        
        logger.debug(f"Initialized validation profile: {self.name}")
        logger.debug(f"Profile settings: {self._profile_settings}")

    def _load_custom_profile(self) -> None:
        """Load custom profile settings from configuration."""
        # Get custom profile settings from configuration
        custom_settings = self.config.get("validation.custom_profile", {})
        
        if not custom_settings:
            logger.warning("Custom profile selected but no custom settings found")
            # Fall back to standard profile settings
            self._profile_settings = self.PROFILES["standard"].copy()
            return
        
        # Start with standard profile settings as defaults
        self._profile_settings = self.PROFILES["standard"].copy()
        
        # Override with custom settings
        self._profile_settings.update(custom_settings)

    def _load_predefined_profile(self) -> None:
        """Load predefined profile settings."""
        self._profile_settings = self.PROFILES[self.name].copy()

    def get(self, setting: str, default: Any = None) -> Any:
        """
        Get a profile setting.
        
        Args:
            setting: Setting name
            default: Default value if setting not found
            
        Returns:
            Setting value or default
        """
        return self._profile_settings.get(setting, default)
    
    def set(self, setting: str, value: Any) -> None:
        """
        Set a profile setting.
        
        Args:
            setting: Setting name
            value: Setting value
        """
        if self.name != "custom":
            logger.warning(f"Cannot modify non-custom profile: {self.name}")
            return
        
        # Update internal settings
        self._profile_settings[setting] = value
        
        # Update the configuration (only for custom profiles)
        custom_profile_path = f"validation.custom_profile.{setting}"
        current_custom_settings = self.config.get("validation.custom_profile", {})
        if not isinstance(current_custom_settings, dict):
            current_custom_settings = {}
        
        # Update the nested dictionary
        updated_settings = current_custom_settings.copy()
        updated_settings[setting] = value
        
        # Store the entire updated custom profile
        self.config.set("validation.custom_profile", updated_settings)
    
    def is_validation_required(self, validation_type: str) -> bool:
        """
        Check if a validation type is required by this profile.
        
        Args:
            validation_type: Type of validation to check
            
        Returns:
            True if validation is required, False otherwise
        """
        validation_level = self._profile_settings.get("validation_level", "medium")
        
        if validation_type == "test":
            # Tests are always required
            return True
        elif validation_type == "lint":
            # Linting is required for all profiles including minimal
            return True
        elif validation_type == "type_check":
            # Type checking is configurable
            return self._profile_settings.get("type_check_required", False)
        elif validation_type == "security":
            # Security scanning is configurable
            return self._profile_settings.get("security_scan_required", False)
        elif validation_type == "performance":
            # Performance checking is configurable
            return self._profile_settings.get("performance_check_required", False)
        
        # Unknown validation type
        logger.warning(f"Unknown validation type: {validation_type}")
        return False
    
    def is_threshold_met(self, validation_type: str, value: float) -> bool:
        """
        Check if a validation value meets the threshold for this profile.
        
        Args:
            validation_type: Type of validation
            value: Value to check
            
        Returns:
            True if the threshold is met, False otherwise
        """
        if validation_type == "test_coverage":
            threshold = self._profile_settings.get("test_coverage_threshold", 0)
            return value >= threshold
        elif validation_type == "complexity":
            threshold = self._profile_settings.get("complexity_threshold", float('inf'))
            return value <= threshold
        elif validation_type == "lint_error":
            threshold = self._profile_settings.get("lint_error_threshold", float('inf'))
            return value <= threshold
        elif validation_type == "lint_warning":
            threshold = self._profile_settings.get("lint_warning_threshold", float('inf'))
            return value <= threshold
        
        # Unknown validation type
        logger.warning(f"Unknown validation threshold type: {validation_type}")
        return True
    
    def should_fail_validation(self, issues: List[Dict[str, Any]]) -> bool:
        """
        Determine if validation should fail based on the issues found.
        
        Args:
            issues: List of validation issues
            
        Returns:
            True if validation should fail, False otherwise
        """
        if not issues:
            return False
        
        # If configured to fail on any issue
        if self._profile_settings.get("fail_on_any_issue", False):
            return len(issues) > 0
        
        # Count errors
        error_count = sum(1 for issue in issues if issue.get("severity", "").lower() == "error")
        
        # If we have errors and they exceed the threshold
        if error_count > self._profile_settings.get("lint_error_threshold", 0):
            return True
        
        return False
    
    def __str__(self) -> str:
        """Get a string representation of the profile."""
        return f"ValidationProfile(name={self.name}, settings={self._profile_settings})"
