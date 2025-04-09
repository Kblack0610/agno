"""
Integration Tests for Multi-Agent System

This module contains integration tests that verify multiple components
of the system working together correctly.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Import components to test
from agents.planning_agent import PlanningAgent
from agents.execution_agent import ExecutionAgent
from agents.test_validation_agent import TestValidationAgent
from core.orchestrator import MultiAgentOrchestrator
from core.message_bus import get_message_bus, reset_message_bus
from core.state_manager import get_state_manager, reset_state_manager

class TestMultiAgentIntegration(unittest.TestCase):
    """
    Integration tests for the multi-agent system.
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
        
        # Create test orchestrator with mock MCP
        self.orchestrator = MultiAgentOrchestrator(
            workspace_dir=self.test_dir,
            use_mock_mcp=True,
            verbose=False
        )
        
        # Set up mocks for agent methods
        self._set_up_mocks()
    
    def tearDown(self):
        """
        Clean up after each test.
        """
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def _set_up_mocks(self):
        """
        Set up mocks for agent methods to control test behavior.
        """
        # Mock planning agent's _create_plan method
        self.mock_plan = {
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
                },
                {
                    "task_id": "task2",
                    "type": "create_file",
                    "description": "Create test file",
                    "path": "test_file.py",
                    "content": "def test_func():\n    return True"
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
        
        # Create the mock methods
        self.orchestrator.planning_agent._create_plan = mock.MagicMock(
            return_value=self.mock_plan
        )
        
        # Track execution calls
        self.executed_tasks = []
        original_execute = self.orchestrator.execution_agent.execute_task
        
        def mock_execute_task(task, **kwargs):
            self.executed_tasks.append(task)
            # Create actual files in the temp directory for validation
            if task.get("type") == "create_file":
                path = os.path.join(self.test_dir, task.get("path", ""))
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w") as f:
                    f.write(task.get("content", ""))
            return {"success": True, "task_id": task.get("task_id")}
        
        self.orchestrator.execution_agent.execute_task = mock_execute_task
        
        # Mock validation results
        self.orchestrator.validation_agent.run_tests = mock.MagicMock(
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
    
    def test_full_workflow(self):
        """
        Test that the full workflow runs correctly from planning to validation.
        """
        # Run the orchestrator
        test_prompt = "Create a simple Python test application"
        result = self.orchestrator.run(
            prompt=test_prompt,
            validation_types=["test"],
            continuous_validation=True
        )
        
        # Check overall result
        self.assertEqual(result["status"], "completed")
        self.assertFalse("error" in result)
        
        # Verify phases were recorded
        workflow_state = get_state_manager().get_namespace("workflow")
        self.assertEqual(workflow_state["prompt"], test_prompt)
        
        # Check each phase's results
        results = result.get("results", {})
        
        # Planning phase
        self.assertTrue(results["plan"]["success"])
        self.assertEqual(
            results["plan"]["plan"]["plan_id"],
            self.mock_plan["plan_id"]
        )
        
        # Execution phase
        self.assertTrue(results["execution"]["success"])
        
        # Validation phase
        self.assertTrue(results["validation"]["success"])
        
        # Check that tasks were executed
        self.assertEqual(len(self.executed_tasks), len(self.mock_plan["tasks"]))
        
        # Verify files were created
        for task in self.mock_plan["tasks"]:
            if task["type"] == "create_file":
                file_path = os.path.join(self.test_dir, task["path"])
                self.assertTrue(
                    os.path.exists(file_path),
                    f"File {file_path} should exist"
                )
    
    def test_workflow_with_failed_planning(self):
        """
        Test workflow behavior when planning fails.
        """
        # Make planning fail
        self.orchestrator.planning_agent._create_plan = mock.MagicMock(
            side_effect=ValueError("Test planning error")
        )
        
        # Run the orchestrator
        test_prompt = "Create a simple Python test application"
        result = self.orchestrator.run(
            prompt=test_prompt,
            validation_types=["test"],
            continuous_validation=True
        )
        
        # Check overall result
        self.assertEqual(result["status"], "failed")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test planning error")
        
        # Verify that no tasks were executed
        self.assertEqual(len(self.executed_tasks), 0)
    
    def test_workflow_with_failed_execution(self):
        """
        Test workflow behavior when execution fails.
        """
        # Make task execution fail
        original_execute = self.orchestrator.execution_agent.execute_task
        
        def failing_execute_task(task, **kwargs):
            if task.get("task_id") == "task2":
                return {
                    "success": False,
                    "task_id": task.get("task_id"),
                    "error": "Test execution error"
                }
            return original_execute(task, **kwargs)
        
        self.orchestrator.execution_agent.execute_task = failing_execute_task
        
        # Run the orchestrator
        test_prompt = "Create a simple Python test application"
        result = self.orchestrator.run(
            prompt=test_prompt,
            validation_types=["test"],
            continuous_validation=True
        )
        
        # Check execution results
        execution_result = result.get("results", {}).get("execution", {})
        self.assertFalse(execution_result.get("success", True))
        
        # Check overall workflow status
        self.assertEqual(result["status"], "failed")
    
    def test_workflow_with_failed_validation(self):
        """
        Test workflow behavior when validation fails.
        """
        # Make validation fail
        self.orchestrator.validation_agent.run_tests = mock.MagicMock(
            return_value={
                "status": "completed",
                "success": False,
                "details": {
                    "tests_run": 2,
                    "tests_passed": 1,
                    "coverage": 50,
                    "failures": ["Test failure"]
                }
            }
        )
        
        # Run the orchestrator
        test_prompt = "Create a simple Python test application"
        result = self.orchestrator.run(
            prompt=test_prompt,
            validation_types=["test"],
            continuous_validation=True
        )
        
        # Check validation results
        validation_result = result.get("results", {}).get("validation", {})
        self.assertFalse(validation_result.get("success", True))
        
        # Check workflow status - should complete with issues
        self.assertEqual(result["status"], "completed_with_issues")
    
    def test_continuous_validation(self):
        """
        Test that continuous validation occurs during execution.
        """
        # Run the orchestrator with continuous validation
        test_prompt = "Create a simple Python test application"
        result = self.orchestrator.run(
            prompt=test_prompt,
            validation_types=["test"],
            continuous_validation=True
        )
        
        # Check execution results for validation results
        execution_result = result.get("results", {}).get("execution", {})
        self.assertIn("validation_results", execution_result)
        self.assertGreater(len(execution_result["validation_results"]), 0)
        
        # Verify validation agent was called multiple times
        self.assertGreater(
            self.orchestrator.validation_agent.run_tests.call_count,
            1
        )
    
    def test_without_continuous_validation(self):
        """
        Test workflow without continuous validation.
        """
        # Run the orchestrator without continuous validation
        test_prompt = "Create a simple Python test application"
        result = self.orchestrator.run(
            prompt=test_prompt,
            validation_types=["test"],
            continuous_validation=False
        )
        
        # Check execution results have no validation results
        execution_result = result.get("results", {}).get("execution", {})
        self.assertNotIn("validation_results", execution_result)
        
        # Verify validation agent was called once (final validation)
        self.assertEqual(
            self.orchestrator.validation_agent.run_tests.call_count,
            1
        )


if __name__ == "__main__":
    unittest.main()
