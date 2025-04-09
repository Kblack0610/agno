"""
Unit tests for the ValidationProfile class.

These tests verify that the validation profiles correctly enforce validation
rules and thresholds based on the profile type.
"""

import unittest
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile

class TestValidationProfile(unittest.TestCase):
    """Tests for the ValidationProfile class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a ConfigManager for testing
        self.config = ConfigManager()
    
    def test_standard_profile(self):
        """Test the standard validation profile."""
        profile = ValidationProfile("standard", self.config)
        
        # Check profile settings
        self.assertEqual(profile.name, "standard")
        self.assertEqual(profile.get("validation_level"), "medium")
        self.assertEqual(profile.get("test_coverage_threshold"), 70)
        self.assertEqual(profile.get("complexity_threshold"), 10)
        self.assertEqual(profile.get("lint_error_threshold"), 0)
        self.assertEqual(profile.get("type_check_required"), True)
        self.assertEqual(profile.get("security_scan_required"), False)
    
    def test_strict_profile(self):
        """Test the strict validation profile."""
        profile = ValidationProfile("strict", self.config)
        
        # Check profile settings
        self.assertEqual(profile.name, "strict")
        self.assertEqual(profile.get("validation_level"), "high")
        self.assertEqual(profile.get("test_coverage_threshold"), 90)
        self.assertEqual(profile.get("complexity_threshold"), 7)
        self.assertEqual(profile.get("fail_on_any_issue"), True)
    
    def test_minimal_profile(self):
        """Test the minimal validation profile."""
        profile = ValidationProfile("minimal", self.config)
        
        # Check profile settings
        self.assertEqual(profile.name, "minimal")
        self.assertEqual(profile.get("validation_level"), "low")
        self.assertEqual(profile.get("test_coverage_threshold"), 50)
        self.assertEqual(profile.get("complexity_threshold"), 15)
        self.assertEqual(profile.get("type_check_required"), False)
    
    def test_unknown_profile_fallback(self):
        """Test that unknown profiles fall back to standard."""
        profile = ValidationProfile("unknown", self.config)
        
        # Should fall back to standard
        self.assertEqual(profile.name, "standard")
        self.assertEqual(profile.get("validation_level"), "medium")
    
    def test_custom_profile(self):
        """Test the custom validation profile."""
        # Set up custom profile settings in the config
        self.config.set("validation.custom_profile.test_coverage_threshold", 75)
        self.config.set("validation.custom_profile.lint_error_threshold", 2)
        
        profile = ValidationProfile("custom", self.config)
        
        # Check that custom settings were applied
        self.assertEqual(profile.name, "custom")
        self.assertEqual(profile.get("test_coverage_threshold"), 75)
        self.assertEqual(profile.get("lint_error_threshold"), 2)
        
        # Check that unspecified settings fall back to defaults
        self.assertEqual(profile.get("validation_level"), "medium")
    
    def test_validation_required(self):
        """Test validation type requirements for different profiles."""
        # Standard profile
        std_profile = ValidationProfile("standard", self.config)
        self.assertTrue(std_profile.is_validation_required("test"))
        self.assertTrue(std_profile.is_validation_required("lint"))
        self.assertTrue(std_profile.is_validation_required("type_check"))
        self.assertFalse(std_profile.is_validation_required("security"))
        
        # Minimal profile
        min_profile = ValidationProfile("minimal", self.config)
        self.assertTrue(min_profile.is_validation_required("test"))
        self.assertTrue(min_profile.is_validation_required("lint"))
        self.assertFalse(min_profile.is_validation_required("type_check"))
        self.assertFalse(min_profile.is_validation_required("security"))
        
        # Strict profile
        strict_profile = ValidationProfile("strict", self.config)
        self.assertTrue(strict_profile.is_validation_required("test"))
        self.assertTrue(strict_profile.is_validation_required("lint"))
        self.assertTrue(strict_profile.is_validation_required("type_check"))
        self.assertTrue(strict_profile.is_validation_required("security"))
        self.assertTrue(strict_profile.is_validation_required("performance"))
    
    def test_threshold_met(self):
        """Test threshold checking for different profiles."""
        # Standard profile
        std_profile = ValidationProfile("standard", self.config)
        self.assertTrue(std_profile.is_threshold_met("test_coverage", 70))
        self.assertTrue(std_profile.is_threshold_met("test_coverage", 80))
        self.assertFalse(std_profile.is_threshold_met("test_coverage", 60))
        
        self.assertTrue(std_profile.is_threshold_met("complexity", 10))
        self.assertTrue(std_profile.is_threshold_met("complexity", 5))
        self.assertFalse(std_profile.is_threshold_met("complexity", 12))
        
        # Strict profile
        strict_profile = ValidationProfile("strict", self.config)
        self.assertTrue(strict_profile.is_threshold_met("test_coverage", 90))
        self.assertFalse(strict_profile.is_threshold_met("test_coverage", 85))
        
        self.assertTrue(strict_profile.is_threshold_met("complexity", 7))
        self.assertFalse(strict_profile.is_threshold_met("complexity", 8))
    
    def test_fail_validation(self):
        """Test validation failure decision for different profiles."""
        # Standard profile - should fail on errors but not warnings
        std_profile = ValidationProfile("standard", self.config)
        
        # No issues
        self.assertFalse(std_profile.should_fail_validation([]))
        
        # Warnings only
        warnings = [{"severity": "warning", "message": "Warning 1"}]
        self.assertFalse(std_profile.should_fail_validation(warnings))
        
        # Errors exceed threshold
        errors = [
            {"severity": "error", "message": "Error 1"},
            {"severity": "error", "message": "Error 2"}
        ]
        self.assertTrue(std_profile.should_fail_validation(errors))
        
        # Strict profile - should fail on any issue
        strict_profile = ValidationProfile("strict", self.config)
        self.assertFalse(strict_profile.should_fail_validation([]))
        self.assertTrue(strict_profile.should_fail_validation(warnings))
        
        # Minimal profile - more lenient
        min_profile = ValidationProfile("minimal", self.config)
        self.assertFalse(min_profile.should_fail_validation([]))
        
        # Less than threshold errors
        few_errors = [{"severity": "error", "message": "Error 1"}]
        self.assertFalse(min_profile.should_fail_validation(few_errors))
        
        # More than threshold errors
        many_errors = [
            {"severity": "error", "message": "Error 1"},
            {"severity": "error", "message": "Error 2"},
            {"severity": "error", "message": "Error 3"},
            {"severity": "error", "message": "Error 4"},
            {"severity": "error", "message": "Error 5"},
            {"severity": "error", "message": "Error 6"}
        ]
        self.assertTrue(min_profile.should_fail_validation(many_errors))
    
    def test_profile_modification(self):
        """Test modifying profile settings."""
        # Custom profile - can be modified
        custom_profile = ValidationProfile("custom", self.config)
        custom_profile.set("test_coverage_threshold", 80)
        self.assertEqual(custom_profile.get("test_coverage_threshold"), 80)
        
        # Standard profile - should not be modifiable
        std_profile = ValidationProfile("standard", self.config)
        std_profile.set("test_coverage_threshold", 80)
        # Should remain unchanged
        self.assertEqual(std_profile.get("test_coverage_threshold"), 70)

if __name__ == "__main__":
    unittest.main()
