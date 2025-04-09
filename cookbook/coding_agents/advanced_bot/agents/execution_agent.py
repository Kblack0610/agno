"""
Execution Agent Module

This agent is responsible for code generation, modification, and execution
based on plans created by the planning agent.
"""

import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# Import from project
from agents.base_agent import BaseAgent
from tools.code_tools import CodeTools
from core.message_bus import Message, get_message_bus
from core.state_manager import get_state_manager

class ExecutionAgent(BaseAgent):
    """
    Agent responsible for code generation and execution.
    
    This agent takes plans from the planning agent and executes them by:
    - Creating and modifying files
    - Managing dependencies
    - Running commands
    - Reporting progress and results
    """
    
    def __init__(
            self,
            name: str = "ExecutionAgent",
            agent_id: str = None,
            config_path: Optional[Union[str, Path]] = None,
            workspace_dir: Optional[Union[str, Path]] = None,
            verbose: bool = False
        ):
        """
        Initialize the execution agent.
        
        Args:
            name: Human-readable name for the agent
            agent_id: Unique identifier for the agent
            config_path: Path to configuration file or directory
            workspace_dir: Directory for code operations
            verbose: Whether to enable verbose logging
        """
        super().__init__(name, agent_id, config_path, verbose)
        
        # Initialize tools
        self.workspace_dir = workspace_dir or Path.cwd()
        self.code_tools = CodeTools(self.workspace_dir)
        
        # Register capabilities
        self.register_capability("file_operations")
        self.register_capability("code_generation")
        self.register_capability("command_execution")
        
        # Set up communication
        self.message_bus = get_message_bus()
        self.message_bus.register_agent(self.agent_id)
        self.message_bus.subscribe(self.agent_id, "plan")
        self.message_bus.subscribe(self.agent_id, "command")
        
        # Track execution state
        self.state_manager = get_state_manager()
        self.update_state({
            "status": "ready",
            "current_task": None,
            "completed_tasks": [],
            "failed_tasks": []
        })
        
        self.logger.info(f"ExecutionAgent initialized with workspace: {self.workspace_dir}")
    
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.
        
        Args:
            context: Dictionary containing input data and state information
            
        Returns:
            Dictionary with the results of the agent's execution
        """
        # Extract plan from context
        plan = context.get("plan", {})
        plan_id = plan.get("plan_id", "unknown")
        tasks = plan.get("tasks", [])
        
        self.logger.info(f"Executing plan {plan_id} with {len(tasks)} tasks")
        
        # Reset execution state for new plan
        self.update_state({
            "status": "executing",
            "plan_id": plan_id,
            "current_task": None,
            "completed_tasks": [],
            "failed_tasks": [],
            "start_time": time.time()
        })
        
        # Execute tasks in sequence
        results = []
        
        for i, task in enumerate(tasks):
            task_id = task.get("task_id", f"task_{i}")
            
            # Update state with current task
            self.update_state({
                "current_task": {
                    "task_id": task_id,
                    "type": task.get("type"),
                    "description": task.get("description"),
                    "status": "executing"
                }
            })
            
            # Execute the task
            self.logger.info(f"Executing task {task_id}: {task.get('description')}")
            
            # Notify start of task
            self._notify_task_status(task, "started")
            
            try:
                result = self._execute_task(task)
                success = result.get("success", False)
                
                # Store task result
                task_result = {
                    "task_id": task_id,
                    "success": success,
                    "result": result
                }
                results.append(task_result)
                
                # Update execution state
                if success:
                    completed = self.state.get("completed_tasks", []) + [task_id]
                    self.update_state({
                        "completed_tasks": completed,
                        "current_task": {
                            "task_id": task_id,
                            "status": "completed"
                        }
                    })
                    
                    # Notify task completion
                    self._notify_task_status(task, "completed", result)
                else:
                    failed = self.state.get("failed_tasks", []) + [task_id]
                    self.update_state({
                        "failed_tasks": failed,
                        "current_task": {
                            "task_id": task_id,
                            "status": "failed",
                            "error": result.get("error")
                        }
                    })
                    
                    # Notify task failure
                    self._notify_task_status(task, "failed", result)
                    
                    # Check if we should continue after failure
                    if not task.get("continue_on_failure", False):
                        self.logger.warning(
                            f"Stopping plan execution due to failed task: {task_id}"
                        )
                        break
            
            except Exception as e:
                self.logger.error(f"Error executing task {task_id}: {e}")
                
                # Update execution state
                failed = self.state.get("failed_tasks", []) + [task_id]
                self.update_state({
                    "failed_tasks": failed,
                    "current_task": {
                        "task_id": task_id,
                        "status": "failed",
                        "error": str(e)
                    }
                })
                
                # Notify task error
                self._notify_task_status(task, "error", {"error": str(e)})
                
                # Add to results
                results.append({
                    "task_id": task_id,
                    "success": False,
                    "error": str(e)
                })
                
                # Check if we should continue after error
                if not task.get("continue_on_failure", False):
                    break
        
        # Finalize execution state
        end_time = time.time()
        execution_time = end_time - self.state.get("start_time", end_time)
        
        completed_count = len(self.state.get("completed_tasks", []))
        failed_count = len(self.state.get("failed_tasks", []))
        total_count = len(tasks)
        
        if failed_count == 0:
            status = "completed"
        elif completed_count > 0:
            status = "partially_completed"
        else:
            status = "failed"
        
        self.update_state({
            "status": status,
            "current_task": None,
            "end_time": end_time,
            "execution_time": execution_time,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "total_count": total_count
        })
        
        # Notify plan completion
        self._notify_plan_status(plan, status, results)
        
        self.logger.info(
            f"Plan execution completed with status: {status} "
            f"({completed_count}/{total_count} tasks successful)"
        )
        
        return {
            "status": status,
            "plan_id": plan_id,
            "completed": completed_count,
            "failed": failed_count,
            "total": total_count,
            "execution_time": execution_time,
            "results": results
        }
    
    def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task based on its type.
        
        Args:
            task: Task dictionary with type and parameters
            
        Returns:
            Result of the task execution
        """
        task_type = task.get("type", "unknown")
        
        # Dispatch to specific task handler based on type
        if task_type == "create_file":
            return self._handle_create_file(task)
        elif task_type == "modify_file":
            return self._handle_modify_file(task)
        elif task_type == "delete_file":
            return self._handle_delete_file(task)
        elif task_type == "run_command":
            return self._handle_run_command(task)
        elif task_type == "install_dependencies":
            return self._handle_install_dependencies(task)
        elif task_type == "generate_code":
            return self._handle_generate_code(task)
        else:
            return {
                "success": False,
                "error": f"Unknown task type: {task_type}"
            }
    
    def _handle_create_file(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task to create a new file.
        
        Args:
            task: Task parameters including path and content
            
        Returns:
            Result of the operation
        """
        file_path = task.get("path")
        content = task.get("content", "")
        make_executable = task.get("executable", False)
        
        if not file_path:
            return {
                "success": False,
                "error": "No file path specified"
            }
        
        # Check if file already exists
        if self.code_tools.file_exists(file_path) and not task.get("overwrite", False):
            return {
                "success": False,
                "error": f"File already exists: {file_path}"
            }
        
        # Create the file
        success = self.code_tools.write_file(
            file_path,
            content,
            create_backup=True,
            make_executable=make_executable
        )
        
        if success:
            return {
                "success": True,
                "path": file_path,
                "size": len(content)
            }
        else:
            return {
                "success": False,
                "error": f"Failed to create file: {file_path}"
            }
    
    def _handle_modify_file(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task to modify an existing file.
        
        Args:
            task: Task parameters including path and modifications
            
        Returns:
            Result of the operation
        """
        file_path = task.get("path")
        
        if not file_path:
            return {
                "success": False,
                "error": "No file path specified"
            }
        
        # Check if file exists
        if not self.code_tools.file_exists(file_path):
            return {
                "success": False,
                "error": f"File does not exist: {file_path}"
            }
        
        # Determine modification type
        mod_type = task.get("modification_type", "replace")
        
        if mod_type == "replace":
            # Full file replacement
            content = task.get("content", "")
            success = self.code_tools.write_file(
                file_path,
                content,
                create_backup=True
            )
            
            if success:
                return {
                    "success": True,
                    "path": file_path,
                    "size": len(content)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to replace file: {file_path}"
                }
                
        elif mod_type == "append":
            # Append to file
            content = task.get("content", "")
            success = self.code_tools.append_to_file(
                file_path,
                content,
                create_backup=True
            )
            
            if success:
                return {
                    "success": True,
                    "path": file_path,
                    "appended": len(content)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to append to file: {file_path}"
                }
                
        elif mod_type == "lines":
            # Modify specific lines
            replacements = []
            
            for mod in task.get("modifications", []):
                start_line = mod.get("start_line", 1)
                end_line = mod.get("end_line", start_line)
                content = mod.get("content", "")
                replacements.append((start_line, end_line, content))
            
            if not replacements:
                return {
                    "success": False,
                    "error": "No line modifications specified"
                }
            
            success = self.code_tools.modify_file(
                file_path,
                replacements,
                create_backup=True
            )
            
            if success:
                return {
                    "success": True,
                    "path": file_path,
                    "modifications": len(replacements)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to modify lines in file: {file_path}"
                }
                
        elif mod_type == "diff":
            # Apply a diff
            diff_content = task.get("diff", "")
            
            if not diff_content:
                return {
                    "success": False,
                    "error": "No diff content specified"
                }
            
            success = self.code_tools.apply_diff(
                file_path,
                diff_content,
                create_backup=True
            )
            
            if success:
                return {
                    "success": True,
                    "path": file_path,
                    "diff_applied": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to apply diff to file: {file_path}"
                }
        
        else:
            return {
                "success": False,
                "error": f"Unknown modification type: {mod_type}"
            }
    
    def _handle_delete_file(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task to delete a file.
        
        Args:
            task: Task parameters including path
            
        Returns:
            Result of the operation
        """
        file_path = task.get("path")
        
        if not file_path:
            return {
                "success": False,
                "error": "No file path specified"
            }
        
        # Check if file exists
        if not self.code_tools.file_exists(file_path):
            return {
                "success": False,
                "error": f"File does not exist: {file_path}"
            }
        
        # Delete the file
        success = self.code_tools.delete_file(
            file_path,
            create_backup=True
        )
        
        if success:
            return {
                "success": True,
                "path": file_path,
                "deleted": True
            }
        else:
            return {
                "success": False,
                "error": f"Failed to delete file: {file_path}"
            }
    
    def _handle_run_command(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task to run a shell command.
        
        Args:
            task: Task parameters including command
            
        Returns:
            Result of the operation
        """
        command = task.get("command")
        
        if not command:
            return {
                "success": False,
                "error": "No command specified"
            }
        
        # Get working directory
        cwd = task.get("cwd", str(self.workspace_dir))
        timeout = task.get("timeout")
        
        # Set up environment
        env = os.environ.copy()
        
        # Add custom environment variables
        if task.get("env"):
            env.update(task["env"])
        
        try:
            # Execute the command
            self.logger.info(f"Running command: {command}")
            
            # Support timeout if specified
            kwargs = {
                "shell": True,
                "cwd": cwd,
                "env": env,
                "capture_output": True,
                "text": True
            }
            
            if timeout:
                kwargs["timeout"] = timeout
            
            result = subprocess.run(command, **kwargs)
            
            # Process the result
            success = result.returncode == 0
            
            return {
                "success": success,
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "cwd": cwd
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "command": command,
                "error": f"Command timed out after {timeout} seconds",
                "timeout": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": str(e)
            }
    
    def _handle_install_dependencies(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task to install dependencies.
        
        Args:
            task: Task parameters including dependencies
            
        Returns:
            Result of the operation
        """
        deps = task.get("dependencies", [])
        dep_type = task.get("dependency_type", "pip")
        
        if not deps:
            return {
                "success": False,
                "error": "No dependencies specified"
            }
        
        if dep_type == "pip":
            # Install Python dependencies using pip
            cmd = [sys.executable, "-m", "pip", "install"]
            
            # Add any options
            options = task.get("options", [])
            if options:
                cmd.extend(options)
            
            # Add dependencies
            cmd.extend(deps)
            
            # Convert to string
            command = " ".join(cmd)
            
            # Run the installation command
            return self._handle_run_command({
                "command": command,
                "cwd": str(self.workspace_dir)
            })
            
        elif dep_type == "npm":
            # Install Node.js dependencies using npm
            cmd = ["npm", "install"]
            
            # Add any options
            options = task.get("options", [])
            if options:
                cmd.extend(options)
            
            # Add dependencies
            cmd.extend(deps)
            
            # Convert to string
            command = " ".join(cmd)
            
            # Run the installation command
            return self._handle_run_command({
                "command": command,
                "cwd": str(self.workspace_dir)
            })
            
        else:
            return {
                "success": False,
                "error": f"Unsupported dependency type: {dep_type}"
            }
    
    def _handle_generate_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task to generate code using external LLM API.
        
        Args:
            task: Task parameters including prompt and target
            
        Returns:
            Result of the operation
        """
        # This is a placeholder for actual code generation
        # In a real implementation, this would call an external LLM API
        prompt = task.get("prompt", "")
        target_file = task.get("target_file")
        
        if not prompt:
            return {
                "success": False,
                "error": "No prompt specified for code generation"
            }
        
        # Simulate code generation
        generated_code = f"# Generated code for prompt: {prompt}\n\n# TODO: Implement actual code generation\n"
        
        # If a target file is specified, write the generated code to it
        if target_file:
            success = self.code_tools.write_file(
                target_file,
                generated_code,
                create_backup=True
            )
            
            if success:
                return {
                    "success": True,
                    "generated": True,
                    "target_file": target_file,
                    "size": len(generated_code)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to write generated code to file: {target_file}"
                }
        
        # Otherwise just return the generated code
        return {
            "success": True,
            "generated": True,
            "code": generated_code
        }
    
    def _notify_task_status(
            self,
            task: Dict[str, Any],
            status: str,
            result: Dict[str, Any] = None
        ) -> None:
        """
        Notify the message bus about task status changes.
        
        Args:
            task: Task that changed status
            status: New status (started, completed, failed, error)
            result: Optional task result
        """
        message = Message(
            sender_id=self.agent_id,
            message_type="task_status",
            content={
                "task_id": task.get("task_id"),
                "status": status,
                "type": task.get("type"),
                "description": task.get("description"),
                "timestamp": time.time(),
                "result": result
            }
        )
        
        self.message_bus.send(message)
    
    def _notify_plan_status(
            self,
            plan: Dict[str, Any],
            status: str,
            results: List[Dict[str, Any]]
        ) -> None:
        """
        Notify the message bus about plan status changes.
        
        Args:
            plan: Plan that changed status
            status: New status (completed, partially_completed, failed)
            results: Task results
        """
        message = Message(
            sender_id=self.agent_id,
            message_type="plan_status",
            content={
                "plan_id": plan.get("plan_id"),
                "status": status,
                "timestamp": time.time(),
                "results": results
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
    agent = ExecutionAgent(verbose=True)
    
    # Create a test plan
    test_plan = {
        "plan_id": "test_plan",
        "tasks": [
            {
                "task_id": "task_1",
                "type": "create_file",
                "description": "Create a test file",
                "path": "test_file.txt",
                "content": "This is a test file."
            },
            {
                "task_id": "task_2",
                "type": "run_command",
                "description": "List files",
                "command": "ls -la"
            },
            {
                "task_id": "task_3",
                "type": "modify_file",
                "description": "Modify the test file",
                "path": "test_file.txt",
                "modification_type": "append",
                "content": "\nThis line was appended."
            }
        ]
    }
    
    # Execute the plan
    result = agent.run({"plan": test_plan})
    
    # Print the result
    print(json.dumps(result, indent=2))
