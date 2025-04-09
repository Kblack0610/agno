#!/usr/bin/env python3
"""
Continuous Validation Bot

This script provides an end-to-end demonstration of the continuous validation bot
with configuration system support.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

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
    parser = argparse.ArgumentParser(description="Continuous Validation Bot")
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="Path to configuration file or directory"
    )
    parser.add_argument(
        "--profile", "-p",
        type=str,
        choices=["strict", "standard", "minimal", "custom"],
        help="Validation profile to use (overrides configuration file)"
    )
    parser.add_argument(
        "--target", "-t",
        type=str,
        required=True,
        help="Target directory or file to validate"
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
    return parser.parse_args()


def setup_environment(args) -> ConfigManager:
    """Set up the environment based on arguments."""
    # Create configuration manager
    config = ConfigManager(args.config)
    
    # Override profile if specified
    if args.profile:
        # Set both environment variable and config value
        os.environ["VALBOT_VALIDATION_PROFILE"] = args.profile
        config.set("validation.profile", args.profile)
    
    # Override verbosity if specified
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        config.set("logging.level", "DEBUG")
    
    return config


def run_validation(args, config: ConfigManager) -> Dict[str, Any]:
    """Run validation based on arguments and configuration."""
    validation_type = args.validation_type
    target_path = args.target
    
    # Get profile from config
    profile_name = config.get("validation.profile", "standard")
    validation_profile = ValidationProfile(profile_name, config)
    
    logger.info(f"Running {validation_type} validation on {target_path} using {profile_name} profile")
    
    # Check if this validation type is required by the profile
    if not validation_profile.is_validation_required(validation_type):
        logger.info(f"Validation type '{validation_type}' is not required by profile '{profile_name}'")
        return {
            "success": True,
            "message": f"Validation '{validation_type}' skipped (not required by {profile_name} profile)"
        }
    
    # Initialize the appropriate agent based on validation type
    if validation_type == "test":
        # Use test validation agent
        agent = TestValidationAgent(config_path=args.config)
        return agent.validate_tests(
            directory=target_path,
            test_type=config.get("test.framework", "pytest"),
            coverage=validation_profile.get("coverage_required", True)
        )
    elif validation_type == "lint":
        # TODO: Create and use Linting Agent
        logger.info("Linting validation is not yet implemented")
        return {"success": False, "message": "Linting validation not implemented"}
    elif validation_type == "type_check":
        # TODO: Create and use Type Checking Agent
        logger.info("Type checking validation is not yet implemented")
        return {"success": False, "message": "Type checking validation not implemented"}
    elif validation_type == "security":
        # TODO: Create and use Security Agent
        logger.info("Security validation is not yet implemented")
        return {"success": False, "message": "Security validation not implemented"}
    elif validation_type == "performance":
        # TODO: Create and use Performance Agent
        logger.info("Performance validation is not yet implemented")
        return {"success": False, "message": "Performance validation not implemented"}
    else:
        # This should never happen due to argparse choices
        return {"success": False, "message": f"Unknown validation type: {validation_type}"}


def main():
    """Main entry point for the continuous validation bot."""
    # Parse command line arguments
    args = parse_args()
    
    # Setup environment and get configuration
    config = setup_environment(args)
    
    # Run validation
    result = run_validation(args, config)
    
    # Display results
    if result.get("success", False):
        logger.info("Validation succeeded!")
        if "message" in result:
            logger.info(result["message"])
    else:
        logger.error("Validation failed!")
        if "message" in result:
            logger.error(result["message"])
    
    # Provide more detailed output if available
    if "output" in result:
        if args.verbose:
            logger.info("Detailed output:")
            print(result["output"])
        else:
            logger.info("Run with --verbose to see detailed output")
    
    # Return appropriate exit code
    return 0 if result.get("success", False) else 1


if __name__ == "__main__":
    exit(main())
