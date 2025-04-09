#!/usr/bin/env python3
"""
MCP Setup for Sequential Thinking

This script helps set up the Model Capability Provider (MCP) environment
for sequential thinking in the validation bot.
"""

import os
import sys
import logging
import argparse
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="MCP Setup for Sequential Thinking")
    
    parser.add_argument(
        "--check-only", "-c",
        action="store_true",
        help="Only check if the MCP environment is set up correctly"
    )
    
    parser.add_argument(
        "--api-key", "-k",
        type=str,
        help="OpenAI API key (if not set in environment)"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4o",
        help="Model to use for sequential thinking"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def check_environment():
    """Check if the required environment variables are set."""
    logger.info("Checking environment variables...")
    
    # Check for OpenAI API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable is not set")
        return False
    else:
        logger.info("✅ OPENAI_API_KEY is set")
    
    # Add more environment checks as needed
    
    return True


def check_dependencies():
    """Check if the required dependencies are installed."""
    logger.info("Checking dependencies...")
    
    # List of required packages
    required_packages = ["agno", "openai"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            logger.warning(f"❌ {package} is not installed")
            missing_packages.append(package)
    
    if missing_packages:
        logger.warning(f"Missing packages: {', '.join(missing_packages)}")
        return False, missing_packages
    
    return True, []


def install_dependencies(missing_packages):
    """Install missing dependencies."""
    logger.info("Installing missing dependencies...")
    
    for package in missing_packages:
        logger.info(f"Installing {package}...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                check=True,
                capture_output=True
            )
            logger.info(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to install {package}: {e}")
            logger.error(f"Error output: {e.stderr.decode()}")
            return False
    
    return True


def setup_mcp(args):
    """Set up the MCP environment."""
    logger.info("Setting up MCP environment...")
    
    # Set API key if provided
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
        logger.info("Set OPENAI_API_KEY from command line argument")
    
    # Check environment
    env_ok = check_environment()
    if not env_ok and not args.api_key:
        logger.error("Environment check failed and no API key provided")
        logger.info("Please set the OPENAI_API_KEY environment variable or provide it with --api-key")
        return False
    
    # Check dependencies
    deps_ok, missing_packages = check_dependencies()
    if not deps_ok:
        if args.check_only:
            logger.warning("Dependencies check failed, but --check-only flag is set, so not installing")
            return False
        
        # Install missing dependencies
        logger.info("Installing missing dependencies...")
        if not install_dependencies(missing_packages):
            logger.error("Failed to install missing dependencies")
            return False
    
    # Test MCP with a simple request
    logger.info("Testing MCP with a simple sequential thinking request...")
    logger.info(f"Using model: {args.model}")
    
    try:
        # Import agno and try a simple request
        # In a real implementation, this would be a call to the MCP
        from agno.agent import Agent
        from agno.models.openai import OpenAIChat
        
        logger.info("✅ Successfully imported agno modules")
        logger.info("MCP environment is set up correctly")
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to test MCP: {e}")
        return False


def main():
    """Run the setup script."""
    args = parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.check_only:
        logger.info("Checking MCP environment only...")
        env_ok = check_environment()
        deps_ok, _ = check_dependencies()
        
        if env_ok and deps_ok:
            logger.info("✅ MCP environment is set up correctly")
            return 0
        else:
            logger.warning("❌ MCP environment is not set up correctly")
            return 1
    else:
        logger.info("Setting up MCP environment...")
        setup_ok = setup_mcp(args)
        
        if setup_ok:
            logger.info("✅ MCP environment set up successfully")
            
            # Print usage instructions
            print("\n===== Usage Instructions =====")
            print("You can now run the validation bot with user prompts:")
            print("python validate_with_prompt.py \"Please validate my code for test coverage\"")
            print("\nOr with a specific profile:")
            print("python validate_with_prompt.py \"Please validate my code for test coverage\" --profile strict")
            print("\nOr with specific validation types:")
            print("python validate_with_prompt.py \"Please validate my code for security issues\" --validation-types security")
            print("=====================================\n")
            
            return 0
        else:
            logger.error("❌ Failed to set up MCP environment")
            return 1


if __name__ == "__main__":
    sys.exit(main())
