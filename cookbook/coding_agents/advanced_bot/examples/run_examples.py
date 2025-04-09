#!/usr/bin/env python3
"""
Validation Bot Example Runner

This script demonstrates end-to-end usage of the validation bot
with different configuration profiles and validation types.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path to make imports work correctly
# when running this script directly
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Now import the validation bot modules
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile
from core.sequential_orchestrator import SequentialOrchestrator
from agents.test_validation_agent import TestValidationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Validation Bot Examples")
    parser.add_argument(
        "--example", "-e",
        type=str,
        choices=["standard", "strict", "minimal", "custom", "env_override"],
        default="standard",
        help="Example to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--target", "-t",
        type=str,
        default=str(Path(__file__).parent),
        help="Target directory to validate (default: this examples directory)"
    )
    return parser.parse_args()


def run_standard_example(target_path, verbose=False):
    """Run validation with standard profile."""
    logger.info("=== Running example with STANDARD profile ===")
    
    config_path = Path(__file__).parent.parent / "config" / "examples" / "standard.yaml"
    logger.info(f"Using configuration: {config_path}")
    
    # Initialize the test validation agent with standard profile
    agent = TestValidationAgent(config_path=config_path)
    
    # Run validation
    result = agent.validate_tests(
        directory=target_path,
        test_type="pytest",
        coverage=True
    )
    
    # Print result summary
    logger.info(f"Validation success: {result.get('success', False)}")
    if verbose and "output" in result:
        print("\nDetailed output:")
        print(result["output"])


def run_strict_example(target_path, verbose=False):
    """Run validation with strict profile."""
    logger.info("=== Running example with STRICT profile ===")
    
    config_path = Path(__file__).parent.parent / "config" / "examples" / "strict.yaml"
    logger.info(f"Using configuration: {config_path}")
    
    # Initialize the test validation agent with strict profile
    agent = TestValidationAgent(config_path=config_path)
    
    # Run validation
    result = agent.validate_tests(
        directory=target_path,
        test_type="pytest",
        coverage=True
    )
    
    # Print result summary
    logger.info(f"Validation success: {result.get('success', False)}")
    if verbose and "output" in result:
        print("\nDetailed output:")
        print(result["output"])


def run_minimal_example(target_path, verbose=False):
    """Run validation with minimal profile."""
    logger.info("=== Running example with MINIMAL profile ===")
    
    config_path = Path(__file__).parent.parent / "config" / "examples" / "minimal.yaml"
    logger.info(f"Using configuration: {config_path}")
    
    # Initialize the test validation agent with minimal profile
    agent = TestValidationAgent(config_path=config_path)
    
    # Run validation
    result = agent.validate_tests(
        directory=target_path,
        test_type="pytest",
        coverage=True
    )
    
    # Print result summary
    logger.info(f"Validation success: {result.get('success', False)}")
    if verbose and "output" in result:
        print("\nDetailed output:")
        print(result["output"])


def run_custom_example(target_path, verbose=False):
    """Run validation with custom profile."""
    logger.info("=== Running example with CUSTOM profile ===")
    
    config_path = Path(__file__).parent.parent / "config" / "examples" / "custom.yaml"
    logger.info(f"Using configuration: {config_path}")
    
    # Initialize the test validation agent with custom profile
    agent = TestValidationAgent(config_path=config_path)
    
    # Run validation
    result = agent.validate_tests(
        directory=target_path,
        test_type="pytest",
        coverage=True
    )
    
    # Print result summary
    logger.info(f"Validation success: {result.get('success', False)}")
    if verbose and "output" in result:
        print("\nDetailed output:")
        print(result["output"])


def run_env_override_example(target_path, verbose=False):
    """Run validation with environment variable overrides."""
    logger.info("=== Running example with ENVIRONMENT VARIABLE overrides ===")
    
    # Set environment variables to override configuration
    os.environ["VALBOT_VALIDATION_PROFILE"] = "custom"
    os.environ["VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD"] = "95"
    os.environ["VALBOT_AGENTS_TEST_VALIDATION_ENABLED"] = "true"
    
    logger.info("Set environment variables:")
    logger.info("  VALBOT_VALIDATION_PROFILE=custom")
    logger.info("  VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD=95")
    logger.info("  VALBOT_AGENTS_TEST_VALIDATION_ENABLED=true")
    
    # Start with standard config but override with env vars
    config_path = Path(__file__).parent.parent / "config" / "examples" / "standard.yaml"
    logger.info(f"Using base configuration: {config_path}")
    
    # Initialize the test validation agent
    agent = TestValidationAgent(config_path=config_path)
    
    # Get the actual profile settings after env var overrides
    config = agent.config
    profile = agent.validation_profile
    
    logger.info(f"Actual profile used: {profile.name}")
    logger.info(f"Test coverage threshold: {profile.get('test_coverage_threshold')}")
    
    # Run validation
    result = agent.validate_tests(
        directory=target_path,
        test_type="pytest",
        coverage=True
    )
    
    # Print result summary
    logger.info(f"Validation success: {result.get('success', False)}")
    if verbose and "output" in result:
        print("\nDetailed output:")
        print(result["output"])
    
    # Clean up environment variables
    del os.environ["VALBOT_VALIDATION_PROFILE"]
    del os.environ["VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD"]
    del os.environ["VALBOT_AGENTS_TEST_VALIDATION_ENABLED"]


def main():
    """Main entry point for the examples."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    target_path = args.target
    
    example_map = {
        "standard": run_standard_example,
        "strict": run_strict_example,
        "minimal": run_minimal_example,
        "custom": run_custom_example,
        "env_override": run_env_override_example,
    }
    
    example_map[args.example](target_path, args.verbose)
    
    return 0


if __name__ == "__main__":
    exit(main())
