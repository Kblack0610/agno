#!/usr/bin/env python3
"""
Multi-Agent System Command Line Interface

This module provides a CLI for interacting with the multi-agent system.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import core components
from core.orchestrator import MultiAgentOrchestrator
from core.message_bus import get_message_bus, reset_message_bus
from core.state_manager import get_state_manager, reset_state_manager
from agents.planning_agent import PlanningAgent
from agents.execution_agent import ExecutionAgent
from agents.test_validation_agent import TestValidationAgent
from config.config_manager import ConfigManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('cli')


def setup_argparser() -> argparse.ArgumentParser:
    """
    Set up the argument parser for the CLI.
    
    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description='Multi-Agent System for Automated Code Development'
    )
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Command to execute'
    )
    
    # Run command - execute full workflow
    run_parser = subparsers.add_parser(
        'run',
        help='Run full multi-agent workflow'
    )
    run_parser.add_argument(
        'prompt',
        help='User prompt to process'
    )
    run_parser.add_argument(
        '--workspace-dir',
        '-w',
        help='Directory for workspace operations',
        default=os.getcwd()
    )
    run_parser.add_argument(
        '--config',
        '-c',
        help='Path to configuration file or directory',
        default=None
    )
    run_parser.add_argument(
        '--validation-types',
        '-v',
        help='Validation types to perform (comma-separated)',
        default='test,lint'
    )
    run_parser.add_argument(
        '--continuous-validation',
        action='store_true',
        help='Perform validation after each task'
    )
    run_parser.add_argument(
        '--mock-mcp',
        action='store_true',
        help='Use mock MCP implementation'
    )
    run_parser.add_argument(
        '--output',
        '-o',
        help='Output file for results (JSON)',
        default=None
    )
    run_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Plan command - only create plan
    plan_parser = subparsers.add_parser(
        'plan',
        help='Create a plan from prompt'
    )
    plan_parser.add_argument(
        'prompt',
        help='User prompt to plan for'
    )
    plan_parser.add_argument(
        '--target-dir',
        '-t',
        help='Target directory for planning',
        default=os.getcwd()
    )
    plan_parser.add_argument(
        '--config',
        '-c',
        help='Path to configuration file or directory',
        default=None
    )
    plan_parser.add_argument(
        '--validation-types',
        '-v',
        help='Validation types to include (comma-separated)',
        default='test,lint'
    )
    plan_parser.add_argument(
        '--mock-mcp',
        action='store_true',
        help='Use mock MCP implementation'
    )
    plan_parser.add_argument(
        '--output',
        '-o',
        help='Output file for plan (JSON)',
        default=None
    )
    plan_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Execute command - execute existing plan
    execute_parser = subparsers.add_parser(
        'execute',
        help='Execute an existing plan'
    )
    execute_parser.add_argument(
        'plan_file',
        help='Path to plan file (JSON)'
    )
    execute_parser.add_argument(
        '--workspace-dir',
        '-w',
        help='Directory for workspace operations',
        default=os.getcwd()
    )
    execute_parser.add_argument(
        '--config',
        '-c',
        help='Path to configuration file or directory',
        default=None
    )
    execute_parser.add_argument(
        '--validation-types',
        '-v',
        help='Validation types to perform (comma-separated)',
        default='test,lint'
    )
    execute_parser.add_argument(
        '--continuous-validation',
        action='store_true',
        help='Perform validation after each task'
    )
    execute_parser.add_argument(
        '--output',
        '-o',
        help='Output file for results (JSON)',
        default=None
    )
    execute_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    # Validate command - validate existing code
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate existing code'
    )
    validate_parser.add_argument(
        'target_dir',
        help='Directory to validate'
    )
    validate_parser.add_argument(
        '--config',
        '-c',
        help='Path to configuration file or directory',
        default=None
    )
    validate_parser.add_argument(
        '--validation-types',
        '-v',
        help='Validation types to perform (comma-separated)',
        default='test,lint'
    )
    validate_parser.add_argument(
        '--output',
        '-o',
        help='Output file for results (JSON)',
        default=None
    )
    validate_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def run_full_workflow(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Run the full multi-agent workflow.
    
    Args:
        args: Command line arguments
        
    Returns:
        Workflow results
    """
    # Set log level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(log_level)
    
    # Parse validation types
    validation_types = [v.strip() for v in args.validation_types.split(',')]
    
    # Reset singletons to ensure clean state
    reset_message_bus()
    reset_state_manager()
    
    # Create orchestrator
    orchestrator = MultiAgentOrchestrator(
        config_path=args.config,
        workspace_dir=args.workspace_dir,
        use_mock_mcp=args.mock_mcp,
        verbose=args.verbose
    )
    
    logger.info(f"Running workflow for prompt: {args.prompt}")
    
    # Run the workflow
    start_time = time.time()
    result = orchestrator.run(
        prompt=args.prompt,
        validation_types=validation_types,
        continuous_validation=args.continuous_validation
    )
    execution_time = time.time() - start_time
    
    # Add execution time
    result["execution_time"] = execution_time
    
    logger.info(f"Workflow completed in {execution_time:.2f} seconds with status: {result.get('status')}")
    
    # Save results if requested
    if args.output:
        save_json(result, args.output)
        logger.info(f"Results saved to {args.output}")
    
    return result


def create_plan(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Create a plan from a prompt.
    
    Args:
        args: Command line arguments
        
    Returns:
        Plan results
    """
    # Set log level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(log_level)
    
    # Parse validation types
    validation_types = [v.strip() for v in args.validation_types.split(',')]
    
    # Reset singletons to ensure clean state
    reset_message_bus()
    reset_state_manager()
    
    # Create planning agent
    agent = PlanningAgent(
        config_path=args.config,
        target_dir=args.target_dir,
        use_mock_mcp=args.mock_mcp,
        verbose=args.verbose
    )
    
    logger.info(f"Creating plan for prompt: {args.prompt}")
    
    # Create the plan
    start_time = time.time()
    result = agent.run({
        "prompt": args.prompt,
        "validation_types": validation_types
    })
    execution_time = time.time() - start_time
    
    # Add execution time
    result["execution_time"] = execution_time
    
    logger.info(f"Plan created in {execution_time:.2f} seconds with status: {'success' if result.get('success') else 'failed'}")
    
    # Save results if requested
    if args.output:
        save_json(result, args.output)
        logger.info(f"Plan saved to {args.output}")
    
    return result


def execute_plan(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Execute an existing plan.
    
    Args:
        args: Command line arguments
        
    Returns:
        Execution results
    """
    # Set log level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(log_level)
    
    # Parse validation types
    validation_types = [v.strip() for v in args.validation_types.split(',')]
    
    # Load plan from file
    try:
        with open(args.plan_file, 'r') as f:
            plan = json.load(f)
    except Exception as e:
        logger.error(f"Error loading plan: {e}")
        return {"success": False, "error": f"Error loading plan: {e}"}
    
    # Check plan structure
    if not isinstance(plan, dict) or "plan" not in plan:
        logger.error("Invalid plan format")
        return {"success": False, "error": "Invalid plan format"}
    
    # Reset singletons to ensure clean state
    reset_message_bus()
    reset_state_manager()
    
    # Create execution agent
    agent = ExecutionAgent(
        config_path=args.config,
        workspace_dir=args.workspace_dir,
        verbose=args.verbose
    )
    
    logger.info(f"Executing plan from {args.plan_file}")
    
    # Execute the plan
    start_time = time.time()
    result = agent.run({"plan": plan.get("plan")})
    execution_time = time.time() - start_time
    
    # Add execution time
    result["execution_time"] = execution_time
    
    logger.info(f"Plan executed in {execution_time:.2f} seconds with status: {'success' if result.get('success') else 'failed'}")
    
    # Validate results if requested
    if args.continuous_validation:
        logger.info("Running validation after execution")
        
        # Create validation agent
        validation_agent = TestValidationAgent(
            config_path=args.config,
            verbose=args.verbose
        )
        
        # Run validation
        validation_result = validation_agent.run_tests(args.workspace_dir)
        
        # Add validation results
        result["validation"] = validation_result
    
    # Save results if requested
    if args.output:
        save_json(result, args.output)
        logger.info(f"Results saved to {args.output}")
    
    return result


def validate_directory(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Validate an existing directory.
    
    Args:
        args: Command line arguments
        
    Returns:
        Validation results
    """
    # Set log level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(log_level)
    
    # Parse validation types
    validation_types = [v.strip() for v in args.validation_types.split(',')]
    
    # Reset singletons to ensure clean state
    reset_message_bus()
    reset_state_manager()
    
    # Create validation agent
    agent = TestValidationAgent(
        config_path=args.config,
        verbose=args.verbose
    )
    
    logger.info(f"Validating directory: {args.target_dir}")
    
    # Run validation
    start_time = time.time()
    result = agent.run_tests(args.target_dir)
    execution_time = time.time() - start_time
    
    # Add execution time
    result["execution_time"] = execution_time
    
    logger.info(f"Validation completed in {execution_time:.2f} seconds with status: {'success' if result.get('success') else 'failed'}")
    
    # Save results if requested
    if args.output:
        save_json(result, args.output)
        logger.info(f"Results saved to {args.output}")
    
    return result


def save_json(data: Dict[str, Any], filename: str) -> None:
    """
    Save data as JSON to a file.
    
    Args:
        data: Data to save
        filename: Output filename
    """
    # Create directory if needed
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    
    # Save the data
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        Exit code
    """
    # Parse arguments
    parser = setup_argparser()
    args = parser.parse_args()
    
    # Check command
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Execute requested command
        if args.command == 'run':
            result = run_full_workflow(args)
        elif args.command == 'plan':
            result = create_plan(args)
        elif args.command == 'execute':
            result = execute_plan(args)
        elif args.command == 'validate':
            result = validate_directory(args)
        else:
            parser.print_help()
            return 1
        
        # Check result
        if not result.get("success", False) and "error" in result:
            logger.error(f"Command failed: {result.get('error')}")
            return 1
        
        return 0
    
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
