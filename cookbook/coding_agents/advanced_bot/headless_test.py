#!/usr/bin/env python3
"""
Headless Testing Script

This script runs tests on individual components with timeouts to prevent hanging.
"""

import os
import sys
import time
import logging
import threading
import signal
import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('headless_test')

# Directory for test output
TEST_OUTPUT_DIR = Path("./test_output_headless")

# Create output directory
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

# Global timeout for any test in seconds
DEFAULT_TIMEOUT = 30

class TestTimeoutError(Exception):
    """Exception raised when a test exceeds its timeout."""
    pass

def run_with_timeout(func: Callable, timeout: int = DEFAULT_TIMEOUT, *args, **kwargs) -> Dict[str, Any]:
    """
    Run a function with a timeout.
    
    Args:
        func: Function to run
        timeout: Timeout in seconds
        args: Positional arguments for func
        kwargs: Keyword arguments for func
        
    Returns:
        Result of the function or error information
    """
    result = {"success": False, "error": None, "data": None}
    completed = threading.Event()
    
    # Thread function
    def target():
        try:
            data = func(*args, **kwargs)
            result["success"] = True
            result["data"] = data
        except Exception as e:
            result["error"] = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Error in test: {str(e)}")
        finally:
            completed.set()
    
    # Start thread
    thread = threading.Thread(target=target)
    thread.daemon = True
    start_time = time.time()
    thread.start()
    
    # Wait for completion or timeout
    completed.wait(timeout=timeout)
    execution_time = time.time() - start_time
    
    if not completed.is_set():
        result["error"] = f"Test timed out after {timeout} seconds"
        logger.error(f"Test timed out after {timeout} seconds")
        return result
    
    result["execution_time"] = execution_time
    return result

def test_message_bus() -> Dict[str, Any]:
    """Test the message bus functionality."""
    from core.message_bus import get_message_bus, reset_message_bus, Message
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
    
    return {"message_bus_test": "passed" if send_success else "failed"}

def test_state_manager() -> Dict[str, Any]:
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
    
    success = (test_value == "test_value" and 
               updated_value == "updated_value" and 
               agent_value == "agent_value")
    
    return {"state_manager_test": "passed" if success else "failed"}

def test_mock_mcp() -> Dict[str, Any]:
    """Test the mock MCP functionality."""
    from mock_mcp import MockMCP
    
    logger.info("Testing MockMCP...")
    
    # Create mock MCP
    mock_mcp = MockMCP(use_real_mcp=False)
    
    # Test sequential thinking
    result = mock_mcp.run_sequential_thinking(
        prompt="Test prompt",
        total_thoughts=3,
        context={"test": "value"}
    )
    
    logger.info(f"MockMCP returned {len(result.get('steps', []))} steps")
    
    success = len(result.get("steps", [])) > 0
    
    return {
        "mock_mcp_test": "passed" if success else "failed",
        "steps_count": len(result.get("steps", []))
    }

def test_validation_agent() -> Dict[str, Any]:
    """Test the validation agent in isolation."""
    from agents.test_validation_agent import TestValidationAgent
    
    logger.info("Testing TestValidationAgent...")
    
    # Create agent
    agent = TestValidationAgent(verbose=True)
    
    # Create a simple test file
    test_dir = TEST_OUTPUT_DIR / "validation_test"
    test_dir.mkdir(exist_ok=True)
    
    test_file = test_dir / "test_simple.py"
    with open(test_file, "w") as f:
        f.write("""
def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3
""")
    
    # Run tests on directory
    result = agent.run_tests(str(test_dir))
    
    logger.info(f"TestValidationAgent result: {result}")
    
    return {
        "validation_agent_test": "passed" if result.get("success", False) else "failed",
        "result": result
    }

def test_planning_agent() -> Dict[str, Any]:
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
        target_dir=TEST_OUTPUT_DIR / "planning_test",
        use_mock_mcp=True,
        verbose=True
    )
    
    # Run with a test prompt
    prompt = "Create a simple Python calculator"
    result = agent.run({"prompt": prompt})
    
    # Check result
    logger.info(f"PlanningAgent result success: {result.get('success', False)}")
    
    return {
        "planning_agent_test": "passed" if result.get("success", False) else "failed",
        "plan_id": result.get("plan_id"),
        "task_count": len(result.get("plan", {}).get("tasks", []))
    }

def test_execution_agent() -> Dict[str, Any]:
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
        workspace_dir=TEST_OUTPUT_DIR / "execution_test",
        verbose=True
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
    
    # Check result
    logger.info(f"ExecutionAgent result success: {result.get('success', False)}")
    
    return {
        "execution_agent_test": "passed" if result.get("success", False) else "failed",
        "task_results": result.get("results", [])
    }

def run_all_tests() -> Dict[str, Any]:
    """Run all tests and return comprehensive results."""
    results = {}
    
    # Start the tests
    logger.info("Starting headless tests...")
    
    # Test message bus
    results["message_bus"] = run_with_timeout(test_message_bus)
    
    # Test state manager
    results["state_manager"] = run_with_timeout(test_state_manager)
    
    # Test mock MCP
    results["mock_mcp"] = run_with_timeout(test_mock_mcp)
    
    # Test validation agent
    results["validation_agent"] = run_with_timeout(test_validation_agent)
    
    # Test planning agent
    results["planning_agent"] = run_with_timeout(test_planning_agent)
    
    # Test execution agent
    results["execution_agent"] = run_with_timeout(test_execution_agent)
    
    # Analyze results
    test_count = len(results)
    success_count = sum(1 for r in results.values() if r.get("success", False))
    logger.info(f"Tests completed: {success_count}/{test_count} successful")
    
    # Save results to file
    with open(TEST_OUTPUT_DIR / "test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
