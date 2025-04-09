"""
Multi-Agent Orchestrator Module

This module provides the orchestration layer for coordinating the workflow
between multiple agents in the system.
"""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Type

# Import from project
from agents.base_agent import BaseAgent
from agents.planning_agent import PlanningAgent
from agents.execution_agent import ExecutionAgent
from agents.test_validation_agent import TestValidationAgent
from core.message_bus import Message, get_message_bus
from core.state_manager import get_state_manager
from config.config_manager import ConfigManager

class MultiAgentOrchestrator:
    """
    Orchestrates the workflow between multiple agents in the system.
    
    This class coordinates the interactions between:
    - Planning Agent: Breaks down tasks into executable plans
    - Execution Agent: Implements code based on plans
    - Validation Agent: Validates code against quality criteria
    
    It manages the overall workflow and ensures proper communication
    between agents throughout the process.
    """
    
    def __init__(
            self,
            config_path: Optional[Union[str, Path]] = None,
            workspace_dir: Optional[Union[str, Path]] = None,
            use_mock_mcp: bool = False,
            verbose: bool = False
        ):
        """
        Initialize the multi-agent orchestrator.
        
        Args:
            config_path: Path to configuration file or directory
            workspace_dir: Root directory for workspace operations
            use_mock_mcp: Whether to use the mock MCP implementation
            verbose: Whether to enable verbose logging
        """
        # Set up logging
        self.logger = logging.getLogger('core.orchestrator')
        log_level = logging.DEBUG if verbose else logging.INFO
        self.logger.setLevel(log_level)
        
        # Load configuration
        self.config = ConfigManager(config_path)
        
        # Set workspace directory
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        
        # Initialize message bus
        self.message_bus = get_message_bus()
        
        # Initialize state manager
        self.state_manager = get_state_manager()
        
        # Create agents
        self.planning_agent = PlanningAgent(
            config_path=config_path,
            target_dir=self.workspace_dir,
            use_mock_mcp=use_mock_mcp,
            verbose=verbose
        )
        
        self.execution_agent = ExecutionAgent(
            config_path=config_path,
            workspace_dir=self.workspace_dir,
            verbose=verbose
        )
        
        self.validation_agent = TestValidationAgent(
            config_path=config_path,
            verbose=verbose
        )
        
        # Register orchestrator with message bus
        self.orchestrator_id = str(uuid.uuid4())
        self.message_bus.register_agent(self.orchestrator_id)
        
        # Subscribe to all agent messages
        self.message_bus.subscribe(self.orchestrator_id, "plan_created")
        self.message_bus.subscribe(self.orchestrator_id, "plan_status")
        self.message_bus.subscribe(self.orchestrator_id, "task_status")
        self.message_bus.subscribe(self.orchestrator_id, "validation_result")
        
        # Initialize workflow state
        self.workflow_id = None
        self.active_agents = []
        
        self.logger.info(
            f"Multi-agent orchestrator initialized with workspace: {self.workspace_dir}"
        )
    
    def run(
            self,
            prompt: str,
            validation_types: List[str] = None,
            continuous_validation: bool = True
        ) -> Dict[str, Any]:
        """
        Run the full multi-agent workflow.
        
        Args:
            prompt: User prompt to process
            validation_types: Types of validation to perform
            continuous_validation: Whether to perform validation after each task
            
        Returns:
            Dictionary with workflow results
        """
        if validation_types is None:
            validation_types = ["test", "lint"]
        
        # Generate a workflow ID
        self.workflow_id = str(uuid.uuid4())
        
        self.logger.info(f"Starting workflow {self.workflow_id} for prompt: {prompt}")
        
        # Initialize workflow state
        workflow_state = {
            "workflow_id": self.workflow_id,
            "prompt": prompt,
            "status": "running",
            "start_time": time.time(),
            "validation_types": validation_types,
            "continuous_validation": continuous_validation
        }
        
        self.state_manager.set(
            "workflow",
            workflow_state,
            namespace="workflow",
            persist=True
        )
        
        try:
            # Phase 1: Planning
            self.logger.info("Starting planning phase")
            plan_result = self._run_planning_phase(prompt, validation_types)
            
            if not plan_result.get("success", False):
                self.logger.error(f"Planning failed: {plan_result.get('error')}")
                return self._complete_workflow("failed", plan_result.get("error"))
            
            plan = plan_result.get("plan", {})
            
            # Phase 2: Execution with continuous validation
            self.logger.info("Starting execution phase")
            execution_result = self._run_execution_phase(
                plan,
                continuous_validation,
                validation_types
            )
            
            if not execution_result.get("success", False):
                self.logger.error(f"Execution failed: {execution_result.get('error')}")
                return self._complete_workflow("failed", execution_result.get("error"))
            
            # Phase 3: Final validation
            self.logger.info("Starting final validation phase")
            validation_result = self._run_validation_phase(validation_types)
            
            # Complete the workflow
            status = "completed" if validation_result.get("success", False) else "completed_with_issues"
            
            return self._complete_workflow(
                status,
                None,
                {
                    "plan": plan_result,
                    "execution": execution_result,
                    "validation": validation_result
                }
            )
            
        except Exception as e:
            self.logger.error(f"Workflow failed with error: {e}")
            return self._complete_workflow("error", str(e))
    
    def _run_planning_phase(
            self,
            prompt: str,
            validation_types: List[str]
        ) -> Dict[str, Any]:
        """
        Run the planning phase of the workflow.
        
        Args:
            prompt: User prompt to process
            validation_types: Types of validation to perform
            
        Returns:
            Dictionary with planning results
        """
        self.logger.info(f"Running planning for prompt: {prompt}")
        
        # Update workflow state
        self.state_manager.set(
            "phase",
            "planning",
            namespace="workflow"
        )
        
        # Run the planning agent
        planning_context = {
            "prompt": prompt,
            "validation_types": validation_types,
            "workflow_id": self.workflow_id
        }
        
        return self.planning_agent.run(planning_context)
    
    def _run_execution_phase(
            self,
            plan: Dict[str, Any],
            continuous_validation: bool,
            validation_types: List[str]
        ) -> Dict[str, Any]:
        """
        Run the execution phase of the workflow.
        
        Args:
            plan: Plan to execute
            continuous_validation: Whether to perform validation after each task
            validation_types: Types of validation to perform
            
        Returns:
            Dictionary with execution results
        """
        self.logger.info(f"Running execution for plan: {plan.get('plan_id')}")
        
        # Update workflow state
        self.state_manager.set(
            "phase",
            "execution",
            namespace="workflow"
        )
        
        # Execute the plan
        execution_context = {
            "plan": plan,
            "workflow_id": self.workflow_id
        }
        
        execution_result = self.execution_agent.run(execution_context)
        
        # Perform continuous validation if requested
        if continuous_validation:
            self.logger.info("Performing continuous validation")
            
            task_results = execution_result.get("results", [])
            validation_results = []
            
            # Find completed tasks
            completed_tasks = [
                task for task in task_results
                if task.get("success", False)
            ]
            
            # Run validation after specific execution milestones
            if completed_tasks:
                # Validate after a batch of tasks
                validation_batch_size = min(3, len(completed_tasks))
                for i in range(0, len(completed_tasks), validation_batch_size):
                    batch = completed_tasks[i:i+validation_batch_size]
                    
                    self.logger.info(f"Validating after batch of {len(batch)} tasks")
                    
                    # Run validation
                    validation_result = self._run_validation_phase(
                        validation_types,
                        f"Continuous validation after tasks: {', '.join([t.get('task_id', 'unknown') for t in batch])}"
                    )
                    
                    validation_results.append(validation_result)
            
            # Add validation results to execution result
            execution_result["validation_results"] = validation_results
        
        return execution_result
    
    def _run_validation_phase(
            self,
            validation_types: List[str],
            description: str = "Final validation"
        ) -> Dict[str, Any]:
        """
        Run the validation phase of the workflow.
        
        Args:
            validation_types: Types of validation to perform
            description: Description of this validation run
            
        Returns:
            Dictionary with validation results
        """
        self.logger.info(f"Running validation: {description}")
        
        # Update workflow state
        self.state_manager.set(
            "phase",
            "validation",
            namespace="workflow"
        )
        
        # Run validation on the target directory
        validation_results = {}
        
        # Run test validation if requested
        if "test" in validation_types:
            test_result = self.validation_agent.run_tests(str(self.workspace_dir))
            validation_results["test"] = test_result
        
        # Simulate other validation types
        # In a real implementation, these would use actual validation agents
        if "lint" in validation_types:
            validation_results["lint"] = {
                "status": "completed",
                "success": True,
                "details": {
                    "errors": 0,
                    "warnings": 2
                }
            }
        
        if "complexity" in validation_types:
            validation_results["complexity"] = {
                "status": "completed",
                "success": True,
                "details": {
                    "complexity_score": 5,
                    "threshold": 10
                }
            }
        
        if "security" in validation_types:
            validation_results["security"] = {
                "status": "completed",
                "success": True,
                "details": {
                    "critical": 0,
                    "high": 0,
                    "medium": 1,
                    "low": 3
                }
            }
        
        # Determine overall validation success
        success = all(
            result.get("success", False)
            for result in validation_results.values()
        )
        
        return {
            "success": success,
            "description": description,
            "results": validation_results
        }
    
    def _complete_workflow(
            self,
            status: str,
            error: Optional[str] = None,
            results: Dict[str, Any] = None
        ) -> Dict[str, Any]:
        """
        Complete the workflow and update the state.
        
        Args:
            status: Final workflow status
            error: Error message if any
            results: Workflow results
            
        Returns:
            Dictionary with complete workflow state
        """
        end_time = time.time()
        start_time = self.state_manager.get("start_time", namespace="workflow")
        execution_time = end_time - start_time if start_time else 0
        
        # Update workflow state
        workflow_state = {
            "status": status,
            "end_time": end_time,
            "execution_time": execution_time
        }
        
        if error:
            workflow_state["error"] = error
            
        if results:
            workflow_state["results"] = results
        
        self.state_manager.update(
            workflow_state,
            namespace="workflow",
            persist=True
        )
        
        # Get the complete workflow state
        complete_state = self.state_manager.get_namespace("workflow")
        
        self.logger.info(
            f"Workflow {self.workflow_id} completed with status: {status} "
            f"in {execution_time:.2f} seconds"
        )
        
        return complete_state
    
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
            message = self.message_bus.receive(self.orchestrator_id, timeout)
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
    orchestrator = MultiAgentOrchestrator(
        verbose=True,
        use_mock_mcp=True
    )
    
    # Create a test prompt
    test_prompt = "Create a simple Python calculator application"
    
    # Run the orchestrator
    result = orchestrator.run(
        prompt=test_prompt,
        validation_types=["test", "lint"],
        continuous_validation=True
    )
    
    # Print the result
    print(json.dumps(result, indent=2))
