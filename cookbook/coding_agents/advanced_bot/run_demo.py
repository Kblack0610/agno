#!/usr/bin/env python3
"""
Advanced Validation Bot Demo

This script demonstrates the end-to-end functionality of the advanced
validation bot with different configuration profiles.
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

# Import validation bot modules
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile
from agents.test_validation_agent import TestValidationAgent


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Advanced Validation Bot Demo")
    
    parser.add_argument(
        "--profile", "-p",
        type=str,
        choices=["standard", "strict", "minimal", "custom"],
        default="standard",
        help="Validation profile to use"
    )
    
    parser.add_argument(
        "--target", "-t",
        type=str,
        default="./config/tests",
        help="Target directory to validate"
    )
    
    parser.add_argument(
        "--validation-type",
        type=str,
        choices=["test", "lint", "type_check", "security", "performance"],
        default="test",
        help="Type of validation to perform"
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


def display_profile_info(profile):
    """Display information about the validation profile."""
    print("\n===== Validation Profile Information =====")
    print(f"Profile Name: {profile.name}")
    print(f"Test Coverage Threshold: {profile.get('test_coverage_threshold')}%")
    print(f"Complexity Threshold: {profile.get('complexity_threshold')}")
    print(f"Lint Error Threshold: {profile.get('lint_error_threshold')}")
    print(f"Lint Warning Threshold: {profile.get('lint_warning_threshold')}")
    print(f"Validation Level: {profile.get('validation_level')}")
    print("Required Validations:")
    print(f"  - Tests: {profile.is_validation_required('test')}")
    print(f"  - Linting: {profile.is_validation_required('lint')}")
    print(f"  - Type Checking: {profile.is_validation_required('type_check')}")
    print(f"  - Security: {profile.is_validation_required('security')}")
    print(f"  - Performance: {profile.is_validation_required('performance')}")
    print("==========================================\n")


def main():
    """Run the demo."""
    args = parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("\n===== Advanced Validation Bot Demo =====")
    print(f"Profile: {args.profile}")
    print(f"Target: {args.target}")
    print(f"Validation Type: {args.validation_type}")
    
    # Determine configuration file path
    config_path = Path(__file__).parent / "config" / "examples" / f"{args.profile}.yaml"
    print(f"Configuration File: {config_path}")
    
    # Set environment variables if requested
    if args.use_env_vars:
        print("\nSetting environment variables to override configuration:")
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
    
    # Initialize validation profile
    profile_name = config.get("validation.profile", "standard")
    validation_profile = ValidationProfile(profile_name, config)
    
    # Display profile information
    display_profile_info(validation_profile)
    
    # Check if validation is required
    if not validation_profile.is_validation_required(args.validation_type):
        print(f"Validation type '{args.validation_type}' is not required by profile '{validation_profile.name}'")
        print("Skipping validation.")
        return 0
    
    # Run appropriate validation based on type
    if args.validation_type == "test":
        print("\n===== Running Test Validation =====")
        agent = TestValidationAgent(config_path=config_path)
        
        # Run test validation
        result = agent.validate_tests(
            directory=args.target,
            test_type="pytest",
            coverage=True
        )
        
        # Display result
        if result.get("success", False):
            print("\n✅ Validation successful!")
        else:
            print("\n❌ Validation failed!")
        
        if args.verbose and "output" in result:
            print("\nDetailed output:")
            print(result["output"])
    elif args.validation_type in ["lint", "type_check", "security", "performance"]:
        print(f"\nNote: {args.validation_type} validation is not implemented in this demo yet.")
        print("To extend this demo, implement the corresponding validation agent.")
    
    # Clean up environment variables
    if args.use_env_vars:
        print("\nCleaning up environment variables...")
        if "VALBOT_VALIDATION_PROFILE" in os.environ:
            del os.environ["VALBOT_VALIDATION_PROFILE"]
        if "VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD" in os.environ:
            del os.environ["VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD"]
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
