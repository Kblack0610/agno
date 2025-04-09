"""
Tests for the PlanningAgent

This module contains unit tests for the PlanningAgent, testing its ability
to break down tasks and create execution plans.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Import components to test
from agents.planning_agent import PlanningAgent
from core.message_bus import get_message_bus, reset_message_bus
from core.state_manager import get_state_manager, reset_state_manager
from mock_mcp import MockMCP

class TestPlanningAgent(unittest.TestCase):
    """
    Test cases for the PlanningAgent.
    """
    
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        # Reset singletons to ensure clean state
        reset_message_bus()
        reset_state_manager()
        
        # Create a temporary directory for tests
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create a test agent with mock MCP
        self.agent = PlanningAgent(
            name="TestPlanningAgent",
            target_dir=self.test_dir,
            use_mock_mcp=True,
            verbose=False
        )
        
        # Set up mock MCP response
        self.mock_mcp_response = {
            "steps": [
                {"thought": "First, I need to understand the core requirements."},
                {"thought": "The user wants a Python calculator. This should include basic operations."},
                {"thought": "Should support addition, subtraction, multiplication, division."},
                {"thought": "Will need a main calculator class with methods for each operation."},
                {"thought": "Input validation is important to handle edge cases."},
                {"thought": "Should include tests for core functionality."},
                {"thought": "Need to consider user interface - command line for simplicity."}
            ]
        }
        
        # Mock the MCP integration
        self.agent.mcp.run_sequential_thinking = mock.MagicMock(
            return_value=self.mock_mcp_response
        )
    
    def tearDown(self):
        """
        Clean up after each test.
        """
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_initialization(self):
        """
        Test that the agent initializes correctly.
        """
        # Check that agent has expected attributes
        self.assertEqual(self.agent.name, "TestPlanningAgent")
        self.assertEqual(self.agent.target_dir, self.test_dir)
        
        # Check that capabilities are registered
        self.assertIn("planning", self.agent.capabilities)
        self.assertIn("sequential_thinking", self.agent.capabilities)
        self.assertIn("task_breakdown", self.agent.capabilities)
        
        # Check that message bus subscriptions are set up
        message_bus = get_message_bus()
        self.assertIn(self.agent.agent_id, message_bus.agents)
        self.assertIn("prompt", message_bus.subscriptions.get(self.agent.agent_id, []))
        self.assertIn("plan_request", message_bus.subscriptions.get(self.agent.agent_id, []))
        
        # Check agent state
        self.assertEqual(self.agent.state.get("status"), "ready")
        self.assertIsNone(self.agent.state.get("current_plan"))
        self.assertEqual(self.agent.state.get("completed_plans"), [])
    
    def test_create_plan(self):
        """
        Test that the agent can create a plan from a prompt.
        """
        # Test prompt
        prompt = "Create a simple Python calculator application"
        
        # Run the agent
        result = self.agent.run({"prompt": prompt})
        
        # Check results
        self.assertTrue(result["success"])
        self.assertIn("plan_id", result)
        self.assertIn("plan", result)
        
        # Check plan structure
        plan = result["plan"]
        self.assertIn("plan_id", plan)
        self.assertEqual(plan["prompt"], prompt)
        self.assertIn("description", plan)
        self.assertIn("tasks", plan)
        self.assertIn("thinking_steps", plan)
        self.assertIn("validation_criteria", plan)
        
        # Verify that tasks were created
        self.assertGreater(len(plan["tasks"]), 0)
        
        # Check for Python-related tasks
        task_paths = [task.get("path", "") for task in plan["tasks"]]
        python_files = [path for path in task_paths if path.endswith(".py")]
        self.assertGreater(len(python_files), 0)
        
        # Check state updates
        self.assertEqual(self.agent.state.get("status"), "completed")
        self.assertIsNotNone(self.agent.state.get("current_plan"))
        
        # Verify MCP was called
        self.agent.mcp.run_sequential_thinking.assert_called_once()
    
    def test_plan_with_different_prompt(self):
        """
        Test that the agent generates different plans for different prompts.
        """
        # Test with web application prompt
        web_prompt = "Create a simple web application with HTML and CSS"
        web_result = self.agent.run({"prompt": web_prompt})
        
        # Get web plan
        web_plan = web_result["plan"]
        web_tasks = web_plan["tasks"]
        
        # Reset agent state
        self.agent.update_state({
            "status": "ready",
            "current_plan": None
        })
        
        # Test with Python application prompt
        py_prompt = "Create a simple Python calculator application"
        py_result = self.agent.run({"prompt": py_prompt})
        
        # Get Python plan
        py_plan = py_result["plan"]
        py_tasks = py_plan["tasks"]
        
        # Plans should be different
        self.assertNotEqual(
            web_tasks,
            py_tasks,
            "Plans for different prompts should be different"
        )
        
        # Web plan should have HTML/CSS files
        web_paths = [task.get("path", "") for task in web_tasks]
        html_files = [path for path in web_paths if path.endswith((".html", ".css"))]
        self.assertGreater(len(html_files), 0)
        
        # Python plan should have Python files
        py_paths = [task.get("path", "") for task in py_tasks]
        py_files = [path for path in py_paths if path.endswith(".py")]
        self.assertGreater(len(py_files), 0)
    
    def test_error_handling(self):
        """
        Test that the agent properly handles errors.
        """
        # Make the MCP raise an exception
        self.agent.mcp.run_sequential_thinking = mock.MagicMock(
            side_effect=ValueError("Test error")
        )
        
        # Run the agent with a valid prompt
        prompt = "Create a simple Python calculator application"
        result = self.agent.run({"prompt": prompt})
        
        # Check results
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test error")
        
        # Check state updates
        self.assertEqual(self.agent.state.get("status"), "error")
        self.assertIn("error", self.agent.state)
        self.assertEqual(self.agent.state.get("error"), "Test error")
    
    def test_empty_prompt(self):
        """
        Test that the agent handles empty prompts gracefully.
        """
        # Run with empty prompt
        result = self.agent.run({"prompt": ""})
        
        # Check results
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "No prompt provided for planning")
        
        # State should not change
        self.assertEqual(self.agent.state.get("status"), "ready")
    
    def test_validation_criteria(self):
        """
        Test that validation criteria are properly generated.
        """
        # Test with various validation types
        validation_types = ["test", "lint", "security"]
        prompt = "Create a simple Python calculator application"
        
        # Run the agent with validation types
        result = self.agent.run({
            "prompt": prompt,
            "validation_types": validation_types
        })
        
        # Check validation criteria
        plan = result["plan"]
        validation_criteria = plan["validation_criteria"]
        
        # Should have all requested validation types
        for validation_type in validation_types:
            self.assertIn(
                validation_type,
                validation_criteria,
                f"Validation criteria should include {validation_type}"
            )
            
        # Should not have unrequested types
        self.assertNotIn(
            "complexity",
            validation_criteria,
            "Validation criteria should not include unrequested types"
        )
    
    def test_message_notification(self):
        """
        Test that the agent notifies the message bus when a plan is created.
        """
        # Get the message bus
        message_bus = get_message_bus()
        
        # Create a test listener
        received_messages = []
        
        def message_listener():
            message = message_bus.receive("test_listener")
            if message:
                received_messages.append(message)
        
        # Register test listener
        message_bus.register_agent("test_listener")
        message_bus.subscribe("test_listener", "plan_created")
        
        # Run the agent
        prompt = "Create a simple Python calculator application"
        result = self.agent.run({"prompt": prompt})
        
        # Check for messages (may need to wait for async processing)
        import time
        for _ in range(5):  # Try a few times
            message_listener()
            if received_messages:
                break
            time.sleep(0.1)
        
        # Should have received a plan_created message
        self.assertGreater(
            len(received_messages),
            0,
            "Should have received at least one message"
        )
        
        # Check message content
        message = received_messages[0]
        self.assertEqual(message.message_type, "plan_created")
        self.assertEqual(message.sender_id, self.agent.agent_id)
        self.assertIn("plan_id", message.content)
        self.assertIn("plan", message.content)
        self.assertEqual(message.content["plan_id"], result["plan_id"])


if __name__ == "__main__":
    unittest.main()
