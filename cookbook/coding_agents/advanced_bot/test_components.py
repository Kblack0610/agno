#!/usr/bin/env python3
"""
Component Testing Script

This script allows for testing individual components of the multi-agent system
to help identify issues and debug problems.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_components')

def test_planning_agent(args):
    """Test the planning agent in isolation."""
    from agents.planning_agent import PlanningAgent
    from core.message_bus import reset_message_bus
    from core.state_manager import reset_state_manager
    
    logger.info("Testing PlanningAgent...")
    
    # Reset singletons
    reset_message_bus()
    reset_state_manager()
    
    # Create agent
    agent = PlanningAgent(
        name="TestPlanningAgent",
        target_dir=args.workspace_dir,
        use_mock_mcp=True,
        verbose=args.verbose
    )
    
    # Run with a test prompt
    prompt = args.prompt or "Create a simple Python calculator"
    result = agent.run({"prompt": prompt})
    
    # Print result summary
    logger.info(f"PlanningAgent test completed with success={result.get('success', False)}")
    if args.show_details:
        import json
        print(json.dumps(result, indent=2))
    
    return result

def test_execution_agent(args):
    """Test the execution agent in isolation."""
    from agents.execution_agent import ExecutionAgent
    from core.message_bus import reset_message_bus
    from core.state_manager import reset_state_manager
    
    logger.info("Testing ExecutionAgent...")
    
    # Reset singletons
    reset_message_bus()
    reset_state_manager()
    
    # Create agent
    agent = ExecutionAgent(
        name="TestExecutionAgent",
        workspace_dir=args.workspace_dir,
        verbose=args.verbose
    )
    
    # Create a simple test plan
    test_plan = {
        "plan_id": "test-plan",
        "prompt": "Test plan",
        "description": "Test execution agent",
        "tasks": [
            {
                "task_id": "task1",
                "type": "create_file",
                "description": "Create test file",
                "path": "test.py",
                "content": "print('Hello, world!')"
            },
            {
                "task_id": "task2",
                "type": "create_file",
                "description": "Create test file",
                "path": "test_file.py",
                "content": "def test_func():\n    return True"
            }
        ]
    }
    
    # Run with test plan
    result = agent.run({"plan": test_plan})
    
    # Print result summary
    logger.info(f"ExecutionAgent test completed with success={result.get('success', False)}")
    if args.show_details:
        import json
        print(json.dumps(result, indent=2))
    
    return result

def test_validation_agent(args):
    """Test the validation agent in isolation."""
    from agents.test_validation_agent import TestValidationAgent
    
    logger.info("Testing TestValidationAgent...")
    
    # Create agent
    agent = TestValidationAgent(
        verbose=args.verbose
    )
    
    # Run tests on directory
    result = agent.run_tests(args.workspace_dir)
    
    # Print result summary
    logger.info(f"TestValidationAgent test completed with success={result.get('success', False)}")
    if args.show_details:
        import json
        print(json.dumps(result, indent=2))
    
    return result

def test_message_bus(args):
    """Test the message bus functionality."""
    from core.message_bus import get_message_bus, reset_message_bus, Message
    import time
    import uuid
    
    logger.info("Testing MessageBus...")
    
    # Reset singleton
    reset_message_bus()
    
    # Get message bus
    message_bus = get_message_bus()
    
    # Create test agents
    agent1_id = f"agent1-{uuid.uuid4()}"
    agent2_id = f"agent2-{uuid.uuid4()}"
    
    # Register agents
    message_bus.register_agent(agent1_id)
    message_bus.register_agent(agent2_id)
    
    # Subscribe to message types
    message_bus.subscribe(agent1_id, "test")
    message_bus.subscribe(agent2_id, "response")
    
    # Create and send test message
    test_message = Message(
        sender_id=agent1_id,
        recipient_id=agent2_id,
        message_type="test",
        content={"text": "Hello, Agent 2!"}
    )
    
    send_success = message_bus.send(test_message)
    logger.info(f"Message sent successfully: {send_success}")
    
    # Attempt to receive the message
    received_message = message_bus.receive(agent2_id)
    
    if received_message:
        logger.info(f"Message received by Agent 2: {received_message.content}")
        
        # Send response
        response_message = received_message.create_response({"text": "Hello, Agent 1!"})
        message_bus.send(response_message)
        
        # Receive response
        response = message_bus.receive(agent1_id)
        if response:
            logger.info(f"Response received by Agent 1: {response.content}")
        else:
            logger.error("No response received by Agent 1")
    else:
        logger.error("No message received by Agent 2")
    
    return send_success

def test_state_manager(args):
    """Test the state manager functionality."""
    from core.state_manager import get_state_manager, reset_state_manager
    
    logger.info("Testing StateManager...")
    
    # Reset singleton
    reset_state_manager()
    
    # Get state manager
    state_manager = get_state_manager()
    
    # Set some test values
    state_manager.set("test_key", "test_value")
    state_manager.set("test_dict", {"name": "test", "value": 123})
    
    # Get values back
    test_value = state_manager.get("test_key")
    test_dict = state_manager.get("test_dict")
    
    logger.info(f"Retrieved test_key: {test_value}")
    logger.info(f"Retrieved test_dict: {test_dict}")
    
    # Test namespaces
    state_manager.set("agent_key", "agent_value", namespace="agents")
    agent_value = state_manager.get("agent_key", namespace="agents")
    
    logger.info(f"Retrieved agent_key from agents namespace: {agent_value}")
    
    # Test updating values
    state_manager.update({"test_key": "updated_value"})
    updated_value = state_manager.get("test_key")
    
    logger.info(f"Updated test_key: {updated_value}")
    
    return test_value == "test_value" and updated_value == "updated_value"

def test_orchestrator(args):
    """Test the orchestrator functionality with mocks."""
    from core.orchestrator import MultiAgentOrchestrator
    from core.message_bus import reset_message_bus
    from core.state_manager import reset_state_manager
    from unittest import mock
    
    logger.info("Testing MultiAgentOrchestrator with mocks...")
    
    # Reset singletons
    reset_message_bus()
    reset_state_manager()
    
    # Create orchestrator with test settings
    orchestrator = MultiAgentOrchestrator(
        workspace_dir=args.workspace_dir,
        use_mock_mcp=True,
        verbose=args.verbose
    )
    
    # Mock the PlanningAgent._create_plan method
    mock_plan = {
        "plan_id": "test-plan-id",
        "prompt": "Test prompt",
        "description": "Test plan for integration",
        "tasks": [
            {
                "task_id": "task1",
                "type": "create_file",
                "description": "Create test file",
                "path": "test.py",
                "content": "print('Hello, world!')"
            }
        ],
        "thinking_steps": [
            {"thought": "Test thought 1"},
            {"thought": "Test thought 2"}
        ],
        "validation_criteria": {
            "test": {
                "required": True,
                "coverage_threshold": 70,
                "failure_threshold": 0
            }
        }
    }
    
    orchestrator.planning_agent._create_plan = mock.MagicMock(
        return_value=mock_plan
    )
    
    # Mock the validation agent
    orchestrator.validation_agent.run_tests = mock.MagicMock(
        return_value={
            "status": "completed",
            "success": True,
            "details": {
                "tests_run": 1,
                "tests_passed": 1,
                "coverage": 80
            }
        }
    )
    
    # Run the orchestrator
    test_prompt = "Test prompt"
    result = orchestrator.run(
        prompt=test_prompt,
        validation_types=["test"],
        continuous_validation=False  # Disable continuous validation to simplify test
    )
    
    # Print result summary
    logger.info(f"Orchestrator test completed with status: {result.get('status')}")
    if args.show_details:
        import json
        print(json.dumps(result, indent=2))
    
    return result

def main():
    """Main entry point for component testing."""
    parser = argparse.ArgumentParser(
        description='Test individual components of the multi-agent system'
    )
    
    parser.add_argument(
        '--component',
        '-c',
        choices=['planning', 'execution', 'validation', 'message_bus', 'state_manager', 'orchestrator', 'all'],
        required=True,
        help='Component to test'
    )
    
    parser.add_argument(
        '--workspace-dir',
        '-w',
        default='./test_output',
        help='Directory for test workspace'
    )
    
    parser.add_argument(
        '--prompt',
        '-p',
        help='Test prompt to use (for planning agent)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--show-details',
        '-d',
        action='store_true',
        help='Show detailed results'
    )
    
    args = parser.parse_args()
    
    # Set log level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger.setLevel(log_level)
    
    # Create workspace directory if it doesn't exist
    os.makedirs(args.workspace_dir, exist_ok=True)
    
    try:
        # Run the selected test
        if args.component == 'planning' or args.component == 'all':
            test_planning_agent(args)
        
        if args.component == 'execution' or args.component == 'all':
            test_execution_agent(args)
        
        if args.component == 'validation' or args.component == 'all':
            test_validation_agent(args)
        
        if args.component == 'message_bus' or args.component == 'all':
            test_message_bus(args)
        
        if args.component == 'state_manager' or args.component == 'all':
            test_state_manager(args)
        
        if args.component == 'orchestrator' or args.component == 'all':
            test_orchestrator(args)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error during component testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
