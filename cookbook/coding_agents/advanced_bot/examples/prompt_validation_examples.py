#!/usr/bin/env python3
"""
Prompt-Based Validation Examples

This script demonstrates various examples of using the prompt-based validation
system with different user prompts and validation profiles.
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Add the parent directory to path to make imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_validation_command(prompt, profile=None, validation_types=None, target=None, verbose=False):
    """
    Run the validation command with the given parameters.
    
    Args:
        prompt: User prompt for validation
        profile: Validation profile (strict, standard, minimal, custom)
        validation_types: Comma-separated list of validation types
        target: Target directory for validation
        verbose: Enable verbose output
    """
    # Base command
    cmd = ["python3", "validate_with_prompt.py", f"\"{prompt}\""]
    
    # Add options
    if profile:
        cmd.append(f"--profile {profile}")
    
    if validation_types:
        cmd.append(f"--validation-types {validation_types}")
    
    if target:
        cmd.append(f"--target {target}")
    
    if verbose:
        cmd.append("--verbose")
    
    # Join command
    cmd_str = " ".join(cmd)
    
    # Print command
    print(f"\n\n{'=' * 40}")
    print(f"EXAMPLE: {prompt}")
    print(f"COMMAND: {cmd_str}")
    print(f"{'=' * 40}\n")
    
    # Run command
    process = subprocess.run(
        cmd_str,
        shell=True,
        cwd=Path(__file__).parent.parent,
        text=True,
        capture_output=True
    )
    
    # Print output
    print(process.stdout)
    
    if process.stderr:
        print(f"ERRORS: {process.stderr}")
    
    return process.returncode


def run_examples():
    """Run all validation examples."""
    examples = [
        {
            "prompt": "Please validate my code for test coverage",
            "profile": "standard",
            "verbose": True
        },
        {
            "prompt": "Check if my code meets security standards",
            "profile": "strict",
            "validation_types": "security,lint",
            "verbose": True
        },
        {
            "prompt": "Validate my tests and code quality",
            "profile": "minimal",
            "validation_types": "test,lint",
            "verbose": True
        },
        {
            "prompt": "Run a quick validation on my code",
            "profile": "minimal",
            "verbose": False
        },
        {
            "prompt": "Perform comprehensive validation on my codebase",
            "profile": "strict",
            "validation_types": "test,lint,security,complexity",
            "verbose": True
        }
    ]
    
    # Run all examples
    for example in examples:
        run_validation_command(
            prompt=example["prompt"],
            profile=example.get("profile"),
            validation_types=example.get("validation_types"),
            target=example.get("target", "."),
            verbose=example.get("verbose", False)
        )
        
        # Add a short delay between examples
        time.sleep(1)


if __name__ == "__main__":
    print("\nRunning Prompt-Based Validation Examples\n")
    run_examples()
    print("\nAll examples completed!\n")
