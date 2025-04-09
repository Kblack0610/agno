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

# Import configuration and validation modules
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile
from core.sequential_orchestrator import SequentialOrchestrator

# MCP imports will be handled dynamically based on user choice


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Prompt-Based Validation Runner")
    
    parser.add_argument(
        "prompt",
        type=str,
        help="User prompt for validation"
    )
    
    parser.add_argument(
        "--profile", "-p",
        type=str,
        default="standard",
        choices=["strict", "standard", "minimal", "custom"],
        help="Validation profile to use"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--target", "-t",
        type=str,
        default=".",
        help="Target directory for validation"
    )
    
    parser.add_argument(
        "--validation-types", "-v",
        type=str,
        default=None,
        help="Comma-separated list of validation types to run"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file for validation results"
    )
    
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4o",
        help="Model to use for validation"
    )
    
    parser.add_argument(
        "--use-real-mcp",
        action="store_true",
        help="Use real MCP instead of mock implementation"
    )
    
    parser.add_argument(
        "--mcp-server-url",
        type=str,
        default=None,
        help="URL of the MCP server (if using real MCP)"
    )
    
    parser.add_argument(
        "--use-agent-bot",
        action="store_true",
        help="Use the multi-agent coder bot instead of MCP-driven validation"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def setup_mcp(use_real_mcp, mcp_server_url=None):
    """
    Set up the MCP implementation based on user choice.
    
    Args:
        use_real_mcp: Whether to use the real MCP
        mcp_server_url: URL of the MCP server if using real MCP
        
    Returns:
        Module containing the MCP implementation
    """
    if use_real_mcp:
        try:
            import mcp_integration
            
            # Test connection to MCP server
            mcp = mcp_integration.MCPIntegration(server_url=mcp_server_url)
            if mcp.is_available():
                print(f"Using real MCP server at {mcp.server_url}")
                return mcp_integration
            else:
                print("Real MCP server not available, falling back to mock implementation")
                import mock_mcp
                return mock_mcp
        except ImportError:
            print("MCP integration module not found, falling back to mock implementation")
            import mock_mcp
            return mock_mcp
    else:
        import mock_mcp
        print("Using mock MCP implementation")
        return mock_mcp


def run_validation(args):
    """
    Run the validation with the given arguments.
    
    Args:
        args: Command line arguments
    """
    # Resolve config path
    config_path = None
    if args.config:
        config_path = Path(args.config)
    elif args.profile != "custom":
        config_path = Path(__file__).parent / "config" / "examples" / f"{args.profile}.yaml"
    
    # Resolve target directory
    target_dir = Path(args.target).resolve()
    
    # Parse validation types
    validation_types = None
    if args.validation_types:
        validation_types = [v.strip() for v in args.validation_types.split(",")]
    
    # Set up MCP
    mcp_module = setup_mcp(args.use_real_mcp, args.mcp_server_url)
    
    # Set environment variables for MCP
    if args.use_real_mcp and args.mcp_server_url:
        os.environ["MCP_SERVER_URL"] = args.mcp_server_url
    
    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Print validation task details
    print("\n===== Validation Task =====")
    print(f"Target Directory: {target_dir}")
    print(f"Validation Types: {', '.join(validation_types) if validation_types else 'Default based on profile'}")
    print(f"Profile: {args.profile}")
    print(f"Configuration: {config_path}")
    print(f"Model: {args.model}")
    if args.use_real_mcp:
        print(f"MCP: Real ({args.mcp_server_url or 'default URL'})")
    else:
        print("MCP: Mock Implementation")
    if args.use_agent_bot:
        print("Using: Multi-Agent Coder Bot")
    else:
        print("Using: MCP-Driven Validation")
    print()
    
    # Initialize validation context
    validation_context = {
        "prompt": args.prompt,
        "target_dir": str(target_dir),
        "validation_types": validation_types,
        "profile": args.profile,
        "model": args.model,
        "use_real_mcp": args.use_real_mcp,
        "mcp_server_url": args.mcp_server_url,
        "use_agent_bot": args.use_agent_bot
    }
    
    # Run validation
    print("===== Running Validation =====")
    print(f"User Prompt: {args.prompt}")
    
    if args.use_agent_bot:
        # Use multi-agent coder bot
        print("Running validation with multi-agent coder bot")
        
        # Import agent modules only when needed
        from agents.test_validation_agent import TestValidationAgent
        
        # Initialize agents
        test_agent = TestValidationAgent(model_id=args.model, config_path=config_path)
        
        # Run validation with agents
        results = {
            "test_validation": test_agent.run_tests(target_dir)
        }
    else:
        # Use MCP-driven validation
        print("Running validation with MCP")
        
        # Initialize orchestrator with the chosen MCP module
        orchestrator = SequentialOrchestrator(
            validation_context=validation_context,
            config_path=config_path
        )
        
        # Monkey patch the mcp2_sequentialthinking function
        # This allows us to switch between mock and real MCP
        orchestrator.mcp2_sequentialthinking = mcp_module.mcp2_sequentialthinking
        
        # Run validation
        results = orchestrator.run(
            prompt=args.prompt,
            target_dir=str(target_dir),
            validation_types=validation_types
        )
    
    # Print results
    print("\n===== Validation Results =====")
    
    # Handle different result structures from different validation methods
    success = False
    
    if isinstance(results, dict):
        # Check if this is the top-level result with a simple success flag
        if "success" in results and isinstance(results["success"], bool):
            success = results["success"]
        # Or it might have a nested structure with details
        elif "details" in results:
            validation_results = results.get("details", {})
            success = all(
                r.get("success", False) 
                for r in validation_results.values() 
                if isinstance(r, dict) and r.get("status") == "completed"
            )
    
    if success:
        print("✅ Validation completed successfully!")
    else:
        print("❌ Validation failed!")
    
    print("\nDetails:")
    if isinstance(results, dict):
        if "details" in results:
            for validation_type, result in results["details"].items():
                print(f"  {validation_type}: {result}")
        else:
            for key, value in results.items():
                print(f"  {key}: {value}")
    else:
        print(f"  {results}")
    
    # Output results to file if requested
    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
    
    return results


def main():
    """Run the validation script."""
    args = parse_args()
    run_validation(args)


if __name__ == "__main__":
    main()
