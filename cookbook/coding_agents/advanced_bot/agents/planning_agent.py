"""
Planning Agent Module

This agent is responsible for breaking down user prompts into executable
plans using sequential thinking capabilities from the MCP integration.
"""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Import from project
from agents.base_agent import BaseAgent
from core.sequential_orchestrator import SequentialOrchestrator
from core.message_bus import Message, get_message_bus
from core.state_manager import get_state_manager
from mock_mcp import MockMCP
from mcp_integration import MCPIntegration

class PlanningAgent(BaseAgent):
    """
    Agent responsible for planning and task breakdown.
    
    This agent uses sequential thinking capabilities to:
    - Break down user prompts into executable tasks
    - Create structured plans for the execution agent
    - Analyze requirements and constraints
    - Determine validation criteria
    """
    
    def __init__(
            self,
            name: str = "PlanningAgent",
            agent_id: str = None,
            config_path: Optional[Union[str, Path]] = None,
            target_dir: Optional[Union[str, Path]] = None,
            use_mock_mcp: bool = False,
            verbose: bool = False
        ):
        """
        Initialize the planning agent.
        
        Args:
            name: Human-readable name for the agent
            agent_id: Unique identifier for the agent
            config_path: Path to configuration file or directory
            target_dir: Target directory for planning operations
            use_mock_mcp: Whether to use the mock MCP implementation
            verbose: Whether to enable verbose logging
        """
        super().__init__(name, agent_id, config_path, verbose)
        
        # Initialize MCP integration
        if use_mock_mcp:
            self.logger.info("Using mock MCP implementation")
            self.mcp = MockMCP(use_real_mcp=False)
        else:
            self.logger.info("Using real MCP integration")
            self.mcp = MCPIntegration()
            
            # Fall back to mock if real MCP is not available
            if not self.mcp.is_available():
                self.logger.warning("Real MCP not available, falling back to mock")
                self.mcp = MockMCP(use_real_mcp=False)
        
        # Initialize sequential orchestrator
        self.target_dir = target_dir or Path.cwd()
        self.orchestrator = SequentialOrchestrator(
            validation_context={"target_dir": str(self.target_dir)},
            config_path=config_path
        )
        
        # Register capabilities
        self.register_capability("planning")
        self.register_capability("sequential_thinking")
        self.register_capability("task_breakdown")
        
        # Set up communication
        self.message_bus = get_message_bus()
        self.message_bus.register_agent(self.agent_id)
        self.message_bus.subscribe(self.agent_id, "prompt")
        self.message_bus.subscribe(self.agent_id, "plan_request")
        
        # Track planning state
        self.state_manager = get_state_manager()
        self.update_state({
            "status": "ready",
            "current_plan": None,
            "completed_plans": []
        })
        
        self.logger.info(f"PlanningAgent initialized with target directory: {self.target_dir}")
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.
        
        Args:
            context: Dictionary containing input data and state information
            
        Returns:
            Dictionary with the results of the agent's execution
        """
        # Extract prompt from context
        prompt = context.get("prompt", "")
        validation_types = context.get("validation_types", ["test", "lint"])
        
        if not prompt:
            return {
                "success": False,
                "error": "No prompt provided for planning"
            }
        
        self.logger.info(f"Planning for prompt: {prompt}")
        
        # Update state for new planning task
        plan_id = context.get("plan_id", str(uuid.uuid4()))
        self.update_state({
            "status": "planning",
            "plan_id": plan_id,
            "prompt": prompt,
            "start_time": time.time()
        })
        
        # Create the plan using sequential thinking
        try:
            plan_result = self._create_plan(prompt, validation_types)
            
            # Update state with plan results
            self.update_state({
                "status": "completed",
                "current_plan": plan_result,
                "end_time": time.time()
            })
            
            # Add to completed plans
            completed_plans = self.state.get("completed_plans", [])
            completed_plans.append({
                "plan_id": plan_id,
                "prompt": prompt,
                "timestamp": time.time()
            })
            self.update_state({
                "completed_plans": completed_plans
            })
            
            # Notify about plan creation
            self._notify_plan_created(plan_id, plan_result)
            
            return {
                "success": True,
                "plan_id": plan_id,
                "plan": plan_result
            }
        
        except Exception as e:
            self.logger.error(f"Error creating plan: {e}")
            
            # Update state with error
            self.update_state({
                "status": "error",
                "error": str(e),
                "end_time": time.time()
            })
            
            return {
                "success": False,
                "plan_id": plan_id,
                "error": str(e)
            }
    
    def _create_plan(
            self,
            prompt: str,
            validation_types: List[str] = None
        ) -> Dict[str, Any]:
        """
        Create a structured plan from a user prompt using sequential thinking.
        
        Args:
            prompt: User prompt to create plan for
            validation_types: Types of validation to include
            
        Returns:
            Structured plan with tasks and validation criteria
        """
        if validation_types is None:
            validation_types = ["test", "lint"]
        
        self.logger.info(f"Creating plan with validation types: {validation_types}")
        
        # Run sequential thinking for planning
        thinking_result = self.mcp.run_sequential_thinking(
            prompt=f"Create a development plan for: {prompt}",
            total_thoughts=7,
            context={
                "target_dir": str(self.target_dir),
                "validation_types": validation_types
            }
        )
        
        # Extract the thinking steps
        steps = thinking_result.get("steps", [])
        
        # Transform thinking steps into a structured plan
        structured_plan = self._transform_to_structured_plan(prompt, steps)
        
        # Add validation criteria
        structured_plan["validation_criteria"] = self._generate_validation_criteria(
            prompt, 
            validation_types
        )
        
        return structured_plan
    
    def _transform_to_structured_plan(
            self,
            prompt: str,
            thinking_steps: List[Dict[str, Any]]
        ) -> Dict[str, Any]:
        """
        Transform sequential thinking steps into a structured plan.
        
        Args:
            prompt: Original user prompt
            thinking_steps: List of sequential thinking steps
            
        Returns:
            Structured plan with tasks
        """
        # Extract thinking content
        thoughts = [step.get("thought", "") for step in thinking_steps if "thought" in step]
        
        if not thoughts:
            raise ValueError("No valid thinking steps provided")
        
        # In a real implementation, we would use LLM to generate structured tasks
        # For now, create some placeholder tasks based on the prompt
        tasks = []
        
        # Simple demonstration task generation - would be much more sophisticated with LLM
        if "web" in prompt.lower() or "website" in prompt.lower():
            tasks.extend([
                {
                    "task_id": "setup_project",
                    "type": "create_file",
                    "description": "Create project structure",
                    "path": "index.html",
                    "content": "<!DOCTYPE html>\n<html>\n<head>\n    <title>Project</title>\n</head>\n<body>\n    <h1>Hello World</h1>\n</body>\n</html>"
                },
                {
                    "task_id": "add_styles",
                    "type": "create_file",
                    "description": "Add CSS styling",
                    "path": "styles.css",
                    "content": "body {\n    font-family: Arial, sans-serif;\n    margin: 20px;\n}"
                },
                {
                    "task_id": "add_script",
                    "type": "create_file",
                    "description": "Add JavaScript functionality",
                    "path": "script.js",
                    "content": "document.addEventListener('DOMContentLoaded', function() {\n    console.log('Page loaded');\n});"
                }
            ])
        elif "python" in prompt.lower() or "script" in prompt.lower():
            tasks.extend([
                {
                    "task_id": "create_main",
                    "type": "create_file",
                    "description": "Create main Python script",
                    "path": "main.py",
                    "content": "def main():\n    print('Hello world!')\n\nif __name__ == '__main__':\n    main()"
                },
                {
                    "task_id": "create_utils",
                    "type": "create_file",
                    "description": "Create utilities module",
                    "path": "utils.py",
                    "content": "def helper_function():\n    return 'Helper function called'"
                },
                {
                    "task_id": "create_tests",
                    "type": "create_file",
                    "description": "Create test file",
                    "path": "test_main.py",
                    "content": "import unittest\nfrom main import main\n\nclass TestMain(unittest.TestCase):\n    def test_main(self):\n        # Add tests here\n        pass\n\nif __name__ == '__main__':\n    unittest.main()"
                }
            ])
        else:
            # Generic tasks
            tasks.extend([
                {
                    "task_id": "create_readme",
                    "type": "create_file",
                    "description": "Create README file",
                    "path": "README.md",
                    "content": f"# Project\n\nThis project was generated from the prompt:\n\n> {prompt}\n\n## Getting Started\n\nInstructions for getting started with this project."
                },
                {
                    "task_id": "initial_setup",
                    "type": "run_command",
                    "description": "Initialize project",
                    "command": "mkdir -p src tests docs"
                }
            ])
        
        # Add some simple logic based on thinking steps
        for thought in thoughts:
            if "database" in thought.lower() or "data storage" in thought.lower():
                tasks.append({
                    "task_id": "setup_database",
                    "type": "create_file",
                    "description": "Create database schema",
                    "path": "schema.sql",
                    "content": "CREATE TABLE users (\n    id INTEGER PRIMARY KEY,\n    name TEXT NOT NULL,\n    email TEXT NOT NULL UNIQUE\n);"
                })
                break
        
        # Create a structured plan
        return {
            "plan_id": str(uuid.uuid4()),
            "prompt": prompt,
            "description": f"Plan generated for: {prompt}",
            "tasks": tasks,
            "thinking_steps": thinking_steps
        }
    
    def _generate_validation_criteria(
            self,
            prompt: str,
            validation_types: List[str]
        ) -> Dict[str, Any]:
        """
        Generate validation criteria based on the prompt and validation types.
        
        Args:
            prompt: User prompt
            validation_types: Types of validation to include
            
        Returns:
            Dictionary of validation criteria
        """
        criteria = {}
        
        if "test" in validation_types:
            criteria["test"] = {
                "required": True,
                "coverage_threshold": 70,
                "failure_threshold": 0
            }
            
        if "lint" in validation_types:
            criteria["lint"] = {
                "required": True,
                "error_threshold": 0,
                "warning_threshold": 5
            }
            
        if "complexity" in validation_types:
            criteria["complexity"] = {
                "required": True,
                "threshold": 10
            }
            
        if "security" in validation_types:
            criteria["security"] = {
                "required": True,
                "critical_threshold": 0,
                "high_threshold": 0,
                "medium_threshold": 3
            }
        
        return criteria
    
    def _notify_plan_created(
            self,
            plan_id: str,
            plan: Dict[str, Any]
        ) -> None:
        """
        Notify the message bus about plan creation.
        
        Args:
            plan_id: ID of the created plan
            plan: The plan that was created
        """
        message = Message(
            sender_id=self.agent_id,
            message_type="plan_created",
            content={
                "plan_id": plan_id,
                "plan": plan,
                "timestamp": time.time()
            }
        )
        
        self.message_bus.send(message)
    
    def receive_messages(self, timeout: float = 0.1) -> List[Message]:
        """
        Receive messages from the message bus.
        
        Args:
            timeout: Maximum time to wait for a message
            
        Returns:
            List of received messages
        """
        messages = []
        while True:
            message = self.message_bus.receive(self.agent_id, timeout)
            if message:
                messages.append(message)
            else:
                break
        
        return messages


# For testing
if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run a simple test
    agent = PlanningAgent(verbose=True, use_mock_mcp=True)
    
    # Create a test prompt
    test_prompt = "Create a simple web application with a form that submits data to a database"
    
    # Execute the planning
    result = agent.run({"prompt": test_prompt})
    
    # Print the result
    print(json.dumps(result, indent=2))
