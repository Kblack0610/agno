"""
Sequential Thinking Orchestrator for Validation Bot

This module manages the integration with the sequential thinking MCP
and orchestrates the validation workflow.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union

# Remove direct agno imports, we'll use dynamic imports or our mock implementation
# from agno.agent import Agent
# from agno.models.openai import OpenAIChat

# Update to absolute imports
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile

class SequentialOrchestrator:
    """
    Orchestrates validation workflows using sequential thinking MCP.
    
    This class provides integration with the sequential thinking MCP
    to manage complex validation workflows with step-by-step reasoning.
    """
    
    def __init__(
        self, 
        validation_context: Dict[str, Any] = None,
        model_id: str = None,
        mcp_endpoint: str = None,
        config_path: Optional[Union[str, Path]] = None
    ):
        """
        Initialize the sequential orchestrator.
        
        Args:
            validation_context: Initial context for validation
            model_id: Model ID to use for reasoning (overrides configuration)
            mcp_endpoint: MCP endpoint URL (if None, uses default)
            config_path: Path to configuration file or directory
        """
        # Initialize configuration
        self.config = ConfigManager(config_path)
        
        # Get configuration values, with arguments taking precedence
        self.validation_context = validation_context or {}
        self.model_id = model_id or self.config.get("model.id", "gpt-4o")
        self.mcp_endpoint = mcp_endpoint or self.config.get("mcp.endpoint", None)
        
        # Initialize validation profile
        profile_name = self.config.get("validation.profile", "standard")
        self.validation_profile = ValidationProfile(profile_name, self.config)
        
        # Track thought history
        self.thought_history = []
        
    def start_validation_chain(
        self, 
        prompt: str,
        validation_type: str,
        initial_context: Dict[str, Any] = None,
        estimated_steps: int = 5
    ) -> Dict[str, Any]:
        """
        Start a validation thought chain using sequential thinking.
        
        Args:
            prompt: Initial prompt for the validation
            validation_type: Type of validation to perform
            initial_context: Optional initial context
            estimated_steps: Estimated number of reasoning steps
            
        Returns:
            Result of the validation chain
        """
        # Check if validation is required based on profile
        if not self.validation_profile.is_validation_required(validation_type):
            return {
                "result": "Validation skipped",
                "reason": f"Validation type '{validation_type}' is not required by profile '{self.validation_profile.name}'",
                "success": True,
                "thought_history": []
            }
            
        # Build context for sequential thinking
        context = {
            "validation_type": validation_type,
            "validation_profile": self.validation_profile.name,
            "thresholds": {
                k: v for k, v in self.validation_profile._profile_settings.items()
                if "threshold" in k
            }
        }
        
        # Add initial context if provided
        if initial_context:
            context.update(initial_context)
            
        # Add any existing validation context
        context.update(self.validation_context)
        
        # Initialize thought chain using MCP sequential thinking
        # In a real implementation, this would call the MCP endpoint
        print(f"Starting validation chain for: {prompt}")
        print(f"Validation type: {validation_type}")
        print(f"Estimated steps: {estimated_steps}")
        
        # First thought in the chain
        current_thought = {
            "thought": f"I need to validate '{prompt}' using {validation_type} validation. " +
                      f"First, I'll analyze the requirements and determine the validation steps.",
            "thoughtNumber": 1,
            "totalThoughts": estimated_steps,
            "nextThoughtNeeded": True,
            "isRevision": False
        }
        
        self.thought_history.append(current_thought)
        
        # In a real implementation, this would continue the thought chain
        # by calling the MCP sequentialthinking tool repeatedly
        
        return {
            "status": "initialized",
            "validation_type": validation_type,
            "thought_history": self.thought_history,
            "context": context
        }
    
    def continue_validation_chain(
        self,
        next_thought: str,
        is_revision: bool = False,
        revises_thought: int = None
    ) -> Dict[str, Any]:
        """
        Continue an existing validation thought chain.
        
        Args:
            next_thought: The next thought in the chain
            is_revision: Whether this thought revises a previous one
            revises_thought: Number of the thought being revised
            
        Returns:
            Updated state of the validation chain
        """
        thought_number = len(self.thought_history) + 1
        
        current_thought = {
            "thought": next_thought,
            "thoughtNumber": thought_number,
            "totalThoughts": max(thought_number, self.thought_history[-1]["totalThoughts"]),
            "nextThoughtNeeded": True,
            "isRevision": is_revision
        }
        
        if is_revision and revises_thought:
            current_thought["revisesThought"] = revises_thought
            
        self.thought_history.append(current_thought)
        
        # In a real implementation, this would call the MCP endpoint
        
        return {
            "status": "in_progress",
            "thought_history": self.thought_history,
            "current_thought": current_thought
        }
    
    def complete_validation_chain(
        self,
        final_thought: str,
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete a validation thought chain with results.
        
        Args:
            final_thought: The final thought in the chain
            validation_results: Results of the validation
            
        Returns:
            Final state of the validation chain with results
        """
        thought_number = len(self.thought_history) + 1
        
        final_thought_obj = {
            "thought": final_thought,
            "thoughtNumber": thought_number,
            "totalThoughts": thought_number,
            "nextThoughtNeeded": False,
            "isRevision": False
        }
        
        self.thought_history.append(final_thought_obj)
        
        return {
            "status": "completed",
            "thought_history": self.thought_history,
            "validation_results": validation_results
        }
    
    def execute_validation_step(
        self,
        thought: Dict[str, Any],
        validation_tools: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        Execute a validation step based on the current thought.
        
        Args:
            thought: The current thought in the chain
            validation_tools: Dictionary of validation tools to use
            
        Returns:
            Results of executing the validation step
        """
        # Parse the thought to determine what validation to perform
        # This is a simplified implementation
        thought_text = thought["thought"].lower()
        
        results = {}
        
        # Determine which validation tools to use based on the thought
        if "run tests" in thought_text or "execute tests" in thought_text:
            if "run_tests" in validation_tools:
                results["test_results"] = validation_tools["run_tests"]()
                
        if "lint code" in thought_text or "code quality" in thought_text:
            if "lint_code" in validation_tools:
                results["lint_results"] = validation_tools["lint_code"]()
                
        if "check types" in thought_text or "type checking" in thought_text:
            if "check_types" in validation_tools:
                results["type_check_results"] = validation_tools["check_types"]()
        
        # Add more validation tool handling here
        
        return {
            "thought": thought,
            "results": results,
            "status": "executed"
        }

    def run(self, prompt=None, target_dir=None, validation_types=None) -> Dict[str, Any]:
        """
        Run the full validation flow with sequential thinking MCP.
        
        This method executes the complete validation workflow by:
        1. Extracting validation requirements from the context
        2. Integrating with the sequential thinking MCP
        3. Running validation tools based on sequential thinking output
        4. Generating a response to the user prompt
        
        Args:
            prompt: User prompt (overrides context)
            target_dir: Target directory for validation (overrides context)
            validation_types: Types of validation to perform (overrides context)
        
        Returns:
            Dictionary containing validation results and response
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract validation parameters from context, with arguments taking precedence
        user_prompt = prompt or self.validation_context.get("user_prompt", "")
        target_directory = target_dir or self.validation_context.get("target_directory", ".")
        
        # Process validation types with proper default handling
        if validation_types:
            if isinstance(validation_types, str):
                validation_types = [vt.strip() for vt in validation_types.split(",")]
        else:
            # Get from context or use default
            validation_types = self.validation_context.get("validation_types", None)
            if validation_types is None:
                validation_types = ["test", "lint"]
        
        # Update validation context with the resolved values
        self.validation_context.update({
            "user_prompt": user_prompt,
            "target_directory": target_directory,
            "validation_types": validation_types
        })
        
        logger.info(f"Starting validation run with prompt: {user_prompt}")
        logger.info(f"Target directory: {target_directory}")
        logger.info(f"Validation types: {validation_types}")
        
        # Set up validation tools
        validation_tools = self._setup_validation_tools()
        
        # Initialize results
        results = {
            "success": True,
            "details": {},
            "steps": []
        }
        
        # Run validation for each type
        for validation_type in validation_types:
            # Check if validation type is required by profile
            if not self.validation_profile.is_validation_required(validation_type):
                logger.info(f"Skipping {validation_type} validation (not required by profile)")
                results["details"][f"{validation_type}_validation"] = {
                    "status": "skipped",
                    "reason": f"Not required by {self.validation_profile.name} profile"
                }
                continue
            
            logger.info(f"Running {validation_type} validation with sequential thinking")
            
            # Start the validation chain with sequential thinking
            validation_chain = self.start_validation_chain(
                prompt=user_prompt,
                validation_type=validation_type,
                initial_context={
                    "target_directory": str(target_directory),
                    "validation_profile": self.validation_profile.name
                },
                estimated_steps=5
            )
            
            # In a real implementation, we would use MCP sequential thinking
            # to continue the chain. For now, we'll simulate with fixed steps.
            try:
                # Call mcp2_sequentialthinking tool
                chain_result = self._run_sequential_thinking(validation_chain, validation_type, validation_tools)
                
                # Add the validation results to overall results
                results["details"][f"{validation_type}_validation"] = chain_result
                
                # Update success flag if any validation fails
                if chain_result.get("success", True) is False:
                    results["success"] = False
                    
                # Add steps to overall steps
                if "steps" in chain_result:
                    results["steps"].extend(chain_result["steps"])
                    
            except Exception as e:
                logger.error(f"Error running {validation_type} validation: {e}")
                results["success"] = False
                results["details"][f"{validation_type}_validation"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Generate a response to the user prompt
        results["response"] = self._generate_response(user_prompt, results)
        
        return results

    def _setup_validation_tools(self) -> Dict[str, Callable]:
        """
        Set up validation tools for the orchestrator.
        
        Returns:
            Dictionary of validation tool functions
        """
        from pathlib import Path
        import subprocess
        import sys
        
        def run_tests():
            """Run tests for the target directory."""
            target_dir = self.validation_context.get("target_directory", ".")
            # This would be implemented with actual test runners
            print(f"Running tests for {target_dir}")
            return {
                "status": "success",
                "coverage": 85,
                "tests_passed": 42,
                "tests_failed": 2
            }
            
        def lint_code():
            """Run linting for the target directory."""
            target_dir = self.validation_context.get("target_directory", ".")
            # This would be implemented with actual linters
            print(f"Linting code in {target_dir}")
            return {
                "status": "success",
                "errors": 0,
                "warnings": 5
            }
            
        def check_types():
            """Run type checking for the target directory."""
            target_dir = self.validation_context.get("target_directory", ".")
            # This would be implemented with actual type checkers
            print(f"Type checking code in {target_dir}")
            return {
                "status": "success",
                "errors": 1
            }
            
        # Return dictionary of validation tools
        return {
            "run_tests": run_tests,
            "lint_code": lint_code,
            "check_types": check_types
        }

    def _run_sequential_thinking(
        self,
        validation_chain: Dict[str, Any],
        validation_type: str,
        validation_tools: Dict[str, Callable]
    ) -> Dict[str, Any]:
        """
        Run sequential thinking for validation using MCP.
        
        Args:
            validation_chain: Initial validation chain
            validation_type: Type of validation to perform
            validation_tools: Dictionary of validation tools
            
        Returns:
            Results of the sequential thinking validation
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Try to import the MCP integration module first, fall back to mock if unavailable
        try:
            # First try to use the real MCP integration if available
            from mcp_integration import mcp2_sequentialthinking
            logger.info("Using real MCP integration for sequential thinking")
        except (ImportError, ConnectionError):
            # Fall back to mock MCP if real MCP is not available
            try:
                from mock_mcp import mcp2_sequentialthinking
                logger.info("Using mock MCP for sequential thinking")
            except ImportError:
                logger.error("Neither real nor mock MCP available")
                return {
                    "status": "error",
                    "error": "MCP implementation not available",
                    "success": False
                }
        
        logger.info(f"Running sequential thinking for {validation_type} validation")
        
        # Start with the initial thought from the validation chain
        thoughts = validation_chain.get("thought_history", [])
        steps = []
        
        if not thoughts:
            return {
                "status": "error",
                "error": "No initial thought provided",
                "success": False
            }
            
        # Add initial thought to steps
        initial_thought = thoughts[0]
        steps.append({
            "thought": initial_thought["thought"],
            "thoughtNumber": initial_thought["thoughtNumber"],
            "totalThoughts": initial_thought["totalThoughts"]
        })
        
        # Instead of fixed thoughts, use the MCP for sequential thinking
        next_thought_needed = True
        current_thought = initial_thought
        
        while next_thought_needed:
            try:
                # Call the sequential thinking function from either the real or mock MCP
                response = mcp2_sequentialthinking(
                    thought=current_thought["thought"],
                    thoughtNumber=current_thought["thoughtNumber"],
                    totalThoughts=current_thought["totalThoughts"],
                    nextThoughtNeeded=True,
                    isRevision=False
                )
                
                # Execute validation step based on current thought if needed
                if "run tests" in current_thought["thought"].lower() or \
                   "execute tests" in current_thought["thought"].lower() or \
                   "lint code" in current_thought["thought"].lower() or \
                   "check types" in current_thought["thought"].lower():
                    # Execute validation step
                    step_result = self.execute_validation_step(current_thought, validation_tools)
                    
                    # Add results to validation context
                    response["results"] = step_result.get("results", {})
                
                # Update current thought with response
                current_thought = response
                
                # Add to steps
                steps.append({
                    "thought": response["thought"],
                    "thoughtNumber": response["thoughtNumber"],
                    "totalThoughts": response["totalThoughts"]
                })
                
                # Check if we need another thought
                next_thought_needed = response.get("nextThoughtNeeded", False)
                
                # Add to thought history
                self.thought_history.append(response)
                
            except Exception as e:
                logger.error(f"Error in sequential thinking: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "success": False,
                    "steps": steps
                }
        
        # Aggregate results from all validation steps
        validation_results = {}
        for thought in self.thought_history:
            if "results" in thought:
                for key, value in thought["results"].items():
                    validation_results[key] = value
        
        return {
            "status": "success",
            "success": True,
            "steps": steps,
            "validation_results": validation_results
        }
        
    def _generate_response(self, prompt: str, results: Dict[str, Any]) -> str:
        """
        Generate a response to the user prompt based on validation results.
        
        Args:
            prompt: User prompt
            results: Validation results
            
        Returns:
            Generated response
        """
        if not prompt:
            return "Validation completed without a specific prompt."
        
        # Create a response based on validation results
        if results.get("success", False):
            response = f"Your code passed all required validations using the {self.validation_profile.name} profile."
        else:
            response = f"Your code did not pass all required validations using the {self.validation_profile.name} profile."
        
        # Add details about test coverage if available
        if "test_validation" in results.get("details", {}):
            test_results = results["details"]["test_validation"]
            if "details" in test_results and "coverage" in test_results["details"]:
                coverage = test_results["details"]["coverage"]
                threshold = self.validation_profile.get("test_coverage_threshold")
                response += f"\n\nTest coverage: {coverage}% (threshold: {threshold}%)"
        
        # Add details about lint validation if available
        if "lint_validation" in results.get("details", {}):
            lint_results = results["details"]["lint_validation"]
            if "details" in lint_results:
                errors = lint_results["details"].get("errors", 0)
                warnings = lint_results["details"].get("warnings", 0)
                response += f"\nLint validation: {errors} errors, {warnings} warnings"
        
        # Add a recommendation based on the prompt and results
        response += f"\n\nBased on your prompt: \"{prompt}\", here's a recommendation:\n"
        
        # This would be a good place to use an LLM for generating a tailored response
        # For now, we'll use a simple template
        if "test" in prompt.lower():
            response += "I recommend focusing on improving your test coverage and test quality."
        elif "lint" in prompt.lower():
            response += "I recommend addressing the lint issues to improve code quality."
        elif "type" in prompt.lower():
            response += "I recommend fixing the type checking issues to improve code robustness."
        elif "security" in prompt.lower():
            response += "I recommend addressing the security vulnerabilities immediately."
        elif "performance" in prompt.lower():
            response += "I recommend profiling your code to identify performance bottlenecks."
        else:
            response += "I recommend reviewing the validation results and addressing the issues based on your project priorities."
        
        return response

# Example usage (will be implemented in separate files)
if __name__ == "__main__":
    # Example orchestrator
    orchestrator = SequentialOrchestrator()
    
    # Start a validation chain
    chain = orchestrator.start_validation_chain(
        prompt="Verify that the calculator module correctly handles division by zero",
        validation_type="unit_testing",
        estimated_steps=3
    )
    
    # Example output
    print(json.dumps(chain, indent=2))
