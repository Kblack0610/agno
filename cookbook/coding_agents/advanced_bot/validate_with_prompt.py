#!/usr/bin/env python3
"""
Prompt-Based Validation Runner

This script runs the validation bot with a user prompt, leveraging the MCP
for sequential thinking and orchestration.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add this directory to path to make imports work correctly
sys.path.insert(0, str(Path(__file__).parent))

# Import mock MCP first to set up the mock modules
import mock_mcp

# Now import validation bot modules
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile
from core.sequential_orchestrator import SequentialOrchestrator


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Prompt-Based Validation Runner")
    
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",
        help="User prompt for the validation task"
    )
    
    parser.add_argument(
        "--prompt-file", "-f",
        type=str,
        help="File containing the user prompt"
    )
    
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
        default=".",
        help="Target directory to validate"
    )
    
    parser.add_argument(
        "--validation-types",
        type=str,
        default="test,lint",
        help="Comma-separated list of validation types to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file for validation results"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="Model to use for sequential thinking"
    )
    
    return parser.parse_args()


def get_user_prompt(args):
    """Get user prompt from command line or file."""
    if args.prompt:
        return args.prompt
    
    if args.prompt_file:
        try:
            with open(args.prompt_file, "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading prompt file: {e}")
            sys.exit(1)
    
    print("Error: Either prompt or prompt file must be provided")
    sys.exit(1)


def setup_validation_context(args, prompt):
    """Set up validation context from arguments and prompt."""
    # Parse validation types
    validation_types = [vt.strip() for vt in args.validation_types.split(",")]
    
    # Create validation context
    context = {
        "user_prompt": prompt,
        "target_directory": Path(args.target).resolve(),
        "validation_types": validation_types,
        "profile": args.profile,
        "model_id": args.model
    }
    
    return context


def run_validation(context: Dict[str, Any], config_path: Optional[Path] = None):
    """Run validation with the given context and configuration."""
    # Determine configuration path
    if not config_path:
        config_path = Path(__file__).parent / "config" / "examples" / f"{context['profile']}.yaml"
    
    # Print validation details
    print("\n===== Validation Task =====")
    print(f"Target Directory: {context['target_directory']}")
    print(f"Validation Types: {', '.join(context['validation_types'])}")
    print(f"Profile: {context['profile']}")
    print(f"Configuration: {config_path}")
    print(f"Model: {context['model_id']}")
    
    # Initialize orchestrator with the configuration
    orchestrator = SequentialOrchestrator(
        validation_context=context,
        config_path=config_path
    )
    
    # Run validation
    print("\n===== Running Validation with MCP =====")
    print(f"User Prompt: {context['user_prompt']}")
    
    try:
        results = orchestrator.run()
        
        # Display results
        print("\n===== Validation Results =====")
        if results.get("success", False):
            print("✅ Validation completed successfully!")
        else:
            print("❌ Validation failed!")
        
        # Print detailed results
        if "details" in results:
            print("\nDetails:")
            for key, value in results["details"].items():
                print(f"  {key}: {value}")
        
        # Print response to prompt
        if "response" in results:
            print("\nResponse to prompt:")
            print(results["response"])
        
        # Save results to file if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
        
        return results
    
    except Exception as e:
        print(f"\n❌ Error running validation: {e}")
        raise


def main():
    """Run the validation task."""
    global args
    args = parse_args()
    
    # Set logging level based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Get user prompt
    prompt = get_user_prompt(args)
    
    # Setup validation context
    context = setup_validation_context(args, prompt)
    
    # Run validation
    try:
        results = run_validation(context)
        return 0 if results.get("success", False) else 1
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
