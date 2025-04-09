#!/usr/bin/env python3
"""
Configuration System Demo

This script demonstrates the capabilities of the configuration system
including profile loading, environment variable overrides, and accessing
configuration values.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add this directory to path to make imports work correctly
sys.path.insert(0, str(Path(__file__).parent))

# Import configuration system modules
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Configuration System Demo")
    
    parser.add_argument(
        "--profile", "-p",
        type=str,
        choices=["standard", "strict", "minimal", "custom"],
        default="standard",
        help="Validation profile to use"
    )
    
    parser.add_argument(
        "--override", "-o",
        type=str,
        help="Override a configuration value (format: key=value)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--use-env-vars",
        action="store_true",
        help="Demonstrate environment variable overrides"
    )
    
    return parser.parse_args()


def display_config_info(config, profile):
    """Display information about the configuration and profile."""
    print("\n===== Configuration Information =====")
    print(f"Configuration File: {config.config_path}")
    
    # Display general configuration
    print("\nGeneral Configuration:")
    print(f"Validation Profile: {config.get('validation.profile')}")
    print(f"Validation Timeout: {config.get('validation.timeout')} seconds")
    print(f"Test Frameworks: {config.get('validation.test_frameworks')}")
    print(f"Logging Level: {config.get('logging.level')}")
    
    # Display agent configuration
    print("\nAgent Configuration:")
    print(f"Test Validation Enabled: {config.get('agents.test_validation.enabled')}")
    print(f"Code Quality Enabled: {config.get('agents.code_quality.enabled')}")
    print(f"Performance Enabled: {config.get('agents.performance.enabled')}")
    print(f"Security Enabled: {config.get('agents.security.enabled')}")
    
    # Display sequential thinking configuration
    print("\nSequential Thinking Configuration:")
    print(f"Enabled: {config.get('sequential_thinking.enabled')}")
    print(f"Max Steps: {config.get('sequential_thinking.max_steps')}")
    
    # Display validation profile information
    print("\nValidation Profile Information:")
    print(f"Profile Name: {profile.name}")
    print(f"Test Coverage Threshold: {profile.get('test_coverage_threshold')}%")
    print(f"Complexity Threshold: {profile.get('complexity_threshold')}")
    print(f"Lint Error Threshold: {profile.get('lint_error_threshold')}")
    print(f"Lint Warning Threshold: {profile.get('lint_warning_threshold')}")
    print(f"Validation Level: {profile.get('validation_level')}")
    
    # Display validation requirements
    print("\nRequired Validations:")
    print(f"  - Tests: {profile.is_validation_required('test')}")
    print(f"  - Linting: {profile.is_validation_required('lint')}")
    print(f"  - Type Checking: {profile.is_validation_required('type_check')}")
    print(f"  - Security: {profile.is_validation_required('security')}")
    print(f"  - Performance: {profile.is_validation_required('performance')}")
    
    print("\n=== Threshold Validation Examples ===")
    # Test coverage examples
    print("Test Coverage Examples:")
    for coverage in [40, 60, 80, 95]:
        result = profile.is_threshold_met("test_coverage", coverage)
        status = "✅ Meets" if result else "❌ Below"
        print(f"  {coverage}% coverage: {status} threshold of {profile.get('test_coverage_threshold')}%")
    
    # Complexity examples
    print("\nComplexity Examples:")
    for complexity in [5, 8, 12, 20]:
        result = profile.is_threshold_met("complexity", complexity)
        status = "✅ Meets" if result else "❌ Exceeds"
        print(f"  Complexity {complexity}: {status} threshold of {profile.get('complexity_threshold')}")
    
    print("=====================================\n")


def main():
    """Run the demo."""
    args = parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n===== Configuration System Demo =====")
    print(f"Profile: {args.profile}")
    
    # Determine configuration file path
    config_path = Path(__file__).parent / "config" / "examples" / f"{args.profile}.yaml"
    print(f"Configuration File: {config_path}")
    
    # Set environment variables if requested
    if args.use_env_vars:
        print("\nSetting environment variables to override configuration:")
        print("  VALBOT_VALIDATION_TIMEOUT=120")
        os.environ["VALBOT_VALIDATION_TIMEOUT"] = "120"
        
        if args.profile == "custom":
            print("  VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD=85")
            os.environ["VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD"] = "85"
        else:
            print("  VALBOT_VALIDATION_PROFILE=custom")
            os.environ["VALBOT_VALIDATION_PROFILE"] = "custom"
            print("  VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD=85")
            os.environ["VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD"] = "85"
    
    # Initialize configuration
    config = ConfigManager(config_path)
    
    # Override a configuration value if specified
    if args.override:
        key, value = args.override.split("=", 1)
        print(f"\nOverriding configuration value: {key} = {value}")
        config.set(key, config._convert_value(value))
    
    # Initialize validation profile
    profile_name = config.get("validation.profile", "standard")
    validation_profile = ValidationProfile(profile_name, config)
    
    # Display configuration and profile information
    display_config_info(config, validation_profile)
    
    # Demonstrate configuration modifications
    print("\n===== Configuration Modification Demo =====")
    
    # Only custom profiles can be modified
    if validation_profile.name == "custom":
        print("Modifying custom profile settings:")
        validation_profile.set("test_coverage_threshold", 88)
        validation_profile.set("complexity_threshold", 9)
        print(f"Updated test coverage threshold: {validation_profile.get('test_coverage_threshold')}%")
        print(f"Updated complexity threshold: {validation_profile.get('complexity_threshold')}")
    else:
        print(f"Cannot modify non-custom profile: {validation_profile.name}")
        print("To modify settings, use the --profile custom option or override with environment variables")
    
    # Demonstrate configuration export
    print("\n===== Configuration Export Demo =====")
    print("\nConfiguration as YAML:")
    print(str(config))
    
    # Clean up environment variables
    if args.use_env_vars:
        print("\nCleaning up environment variables...")
        if "VALBOT_VALIDATION_PROFILE" in os.environ:
            del os.environ["VALBOT_VALIDATION_PROFILE"]
        if "VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD" in os.environ:
            del os.environ["VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD"]
        if "VALBOT_VALIDATION_TIMEOUT" in os.environ:
            del os.environ["VALBOT_VALIDATION_TIMEOUT"]
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
