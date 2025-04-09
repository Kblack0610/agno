"""
Coder Bot Agent

This agent specializes in coding tasks including code generation, modification,
debugging, and analysis using various development tools.
"""

import os
import subprocess
import difflib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from agno.knowledge.url import UrlKnowledge
from agno.embedder.openai import OpenAIEmbedder
from agno.vectordb.lancedb import LanceDb, SearchType

class CodingTools:
    """Tools for coding tasks."""
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read the contents of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file contents
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "error": str(e)
            }
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            
        Returns:
            Dictionary with result information
        """
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_directory(self, directory: str) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            directory: Directory path
            
        Returns:
            Dictionary with directory contents
        """
        try:
            items = []
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                item_info = {
                    "name": item,
                    "path": item_path,
                    "type": "directory" if os.path.isdir(item_path) else "file"
                }
                
                if item_info["type"] == "file":
                    item_info["size"] = os.path.getsize(item_path)
                    # Get file extension
                    _, ext = os.path.splitext(item)
                    item_info["extension"] = ext.lstrip('.')
                
                items.append(item_info)
            
            return {
                "success": True,
                "items": items,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "items": [],
                "error": str(e)
            }
    
    def find_files(
        self, 
        directory: str, 
        pattern: str = None,
        extension: str = None
    ) -> Dict[str, Any]:
        """
        Find files in a directory matching a pattern.
        
        Args:
            directory: Directory to search
            pattern: Pattern to match
            extension: File extension to filter by
            
        Returns:
            Dictionary with found files
        """
        try:
            matches = []
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check if the file matches the pattern
                    pattern_match = True
                    if pattern and pattern not in file:
                        pattern_match = False
                    
                    # Check if the file has the right extension
                    extension_match = True
                    if extension:
                        file_ext = os.path.splitext(file)[1].lstrip('.')
                        if file_ext != extension:
                            extension_match = False
                    
                    if pattern_match and extension_match:
                        matches.append(file_path)
            
            return {
                "success": True,
                "matches": matches,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "matches": [],
                "error": str(e)
            }
    
    def run_command(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """
        Run a shell command.
        
        Args:
            command: Command to run
            cwd: Working directory
            
        Returns:
            Dictionary with command output
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def run_python(self, code: str) -> Dict[str, Any]:
        """
        Run Python code and return the result.
        
        Args:
            code: Python code to run
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Create a temporary file
            tmp_file = Path("temp_script.py")
            with open(tmp_file, 'w') as f:
                f.write(code)
            
            # Run the Python code
            result = subprocess.run(
                ["python", str(tmp_file)],
                capture_output=True,
                text=True
            )
            
            # Remove the temporary file
            os.remove(tmp_file)
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def install_package(self, package: str) -> Dict[str, Any]:
        """
        Install a Python package using pip.
        
        Args:
            package: Package to install
            
        Returns:
            Dictionary with installation results
        """
        try:
            result = subprocess.run(
                ["pip", "install", package],
                capture_output=True,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def get_diff(self, old_content: str, new_content: str) -> Dict[str, Any]:
        """
        Get the diff between two pieces of content.
        
        Args:
            old_content: Original content
            new_content: New content
            
        Returns:
            Dictionary with diff information
        """
        try:
            old_lines = old_content.splitlines()
            new_lines = new_content.splitlines()
            
            diff = list(difflib.unified_diff(
                old_lines,
                new_lines,
                lineterm='',
                fromfile='old',
                tofile='new'
            ))
            
            return {
                "success": True,
                "diff": '\n'.join(diff),
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "diff": "",
                "error": str(e)
            }
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze code for quality issues using specified tools.
        
        Args:
            code: Code to analyze
            
        Returns:
            Dictionary with analysis results
        """
        # This function would integrate with the validation primitives
        # but for now we'll just return a placeholder
        return {
            "success": True,
            "analysis": "Code analysis would be performed here",
            "issues": []
        }

class CoderBot:
    """
    Agent specialized in coding tasks.
    
    This agent can perform various coding tasks including:
    - Code generation and modification
    - Debugging and analysis
    - Running tests and commands
    - Managing project files
    """
    
    def __init__(
        self,
        model_id: str = "gpt-4o",
        work_dir: str = None,
        storage_dir: str = None,
        show_tool_calls: bool = True
    ):
        """
        Initialize the coder bot.
        
        Args:
            model_id: Model ID to use for coding
            work_dir: Working directory for the bot
            storage_dir: Directory for storage and knowledge bases
            show_tool_calls: Whether to show tool calls in output
        """
        self.work_dir = work_dir or os.getcwd()
        self.storage_dir = storage_dir or os.path.join(self.work_dir, '.coding_bot')
        os.makedirs(self.storage_dir, exist_ok=True)
        
        self.tools = CodingTools()
        
        # Setup storage
        self.storage = SqliteStorage(
            table_name="coding_bot_sessions",
            db_file=os.path.join(self.storage_dir, "sessions.db")
        )
        
        # Setup knowledge base
        self.knowledge = None
        
        # Setup agent
        self.agent = Agent(
            name="Coder Bot",
            model=OpenAIChat(id=model_id),
            description="An agent that specializes in coding tasks",
            instructions="""
            You are a Coder Bot that specializes in coding tasks including
            code generation, modification, debugging, and analysis.
            
            Your capabilities include:
            1. Reading and writing files
            2. Analyzing code for quality issues
            3. Running commands and executing code
            4. Installing dependencies
            5. Searching for files and patterns
            
            Follow these guidelines when coding:
            - Write clean, well-documented code
            - Follow best practices for the specific language
            - Include appropriate error handling
            - Write modular, maintainable code
            - Include comments explaining complex logic
            
            When generating code:
            - Consider edge cases and error conditions
            - Include necessary imports and dependencies
            - Add docstrings and type hints in Python
            - Structure code logically with appropriate functions/classes
            
            When debugging:
            - Analyze error messages carefully
            - Check common issues first
            - Suggest multiple solutions when appropriate
            - Verify fixes with tests
            
            When modifying existing code:
            - Understand the existing structure and patterns
            - Maintain consistent style and conventions
            - Document your changes
            - Consider potential side effects
            
            Format your responses with clear explanations of:
            - What you're doing and why
            - Key decisions and trade-offs
            - Any assumptions you're making
            - Next steps or additional improvements
            """,
            tools=[self.tools],
            storage=self.storage,
            show_tool_calls=show_tool_calls,
            markdown=True,
        )
    
    def generate_code(
        self,
        description: str,
        language: str = "python",
        file_path: str = None
    ) -> Dict[str, Any]:
        """
        Generate code based on a description.
        
        Args:
            description: Description of the code to generate
            language: Programming language
            file_path: Path to save the generated code
            
        Returns:
            Dictionary with generated code
        """
        prompt = f"""
        Generate {language} code based on the following description:
        
        {description}
        
        Please create complete, well-structured, and documented code that meets this description.
        Include all necessary imports, error handling, and appropriate comments.
        """
        
        response = self.agent.run(prompt)
        
        # Extract code from the response
        # This is a simple implementation - a more robust one would parse
        # markdown code blocks correctly
        code_lines = []
        in_code_block = False
        
        for line in response.split('\n'):
            if line.startswith('```') and language in line:
                in_code_block = True
                continue
            elif line.startswith('```') and in_code_block:
                in_code_block = False
                continue
            
            if in_code_block:
                code_lines.append(line)
        
        code = '\n'.join(code_lines)
        
        # Save the code if a file path is provided
        if file_path:
            self.tools.write_file(file_path, code)
        
        return {
            "code": code,
            "explanation": response,
            "file_path": file_path
        }
    
    def modify_code(
        self,
        file_path: str,
        modification_description: str
    ) -> Dict[str, Any]:
        """
        Modify existing code based on a description.
        
        Args:
            file_path: Path to the file to modify
            modification_description: Description of the modifications to make
            
        Returns:
            Dictionary with modification results
        """
        # Read the existing code
        file_result = self.tools.read_file(file_path)
        
        if not file_result["success"]:
            return {
                "success": False,
                "error": file_result["error"]
            }
        
        existing_code = file_result["content"]
        
        # Get the file extension and determine the language
        _, ext = os.path.splitext(file_path)
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.rb': 'ruby'
        }
        language = language_map.get(ext, 'python')
        
        prompt = f"""
        Modify the following {language} code according to this description:
        
        {modification_description}
        
        Existing code:
        ```{language}
        {existing_code}
        ```
        
        Please provide the complete modified code, preserving any functionality not mentioned
        in the modification description. Include comments to explain significant changes.
        """
        
        response = self.agent.run(prompt)
        
        # Extract code from the response
        code_lines = []
        in_code_block = False
        
        for line in response.split('\n'):
            if line.startswith('```') and language in line:
                in_code_block = True
                continue
            elif line.startswith('```') and in_code_block:
                in_code_block = False
                continue
            
            if in_code_block:
                code_lines.append(line)
        
        modified_code = '\n'.join(code_lines)
        
        # Get the diff
        diff_result = self.tools.get_diff(existing_code, modified_code)
        
        # Write the modified code back to the file
        write_result = self.tools.write_file(file_path, modified_code)
        
        return {
            "success": write_result["success"],
            "original_code": existing_code,
            "modified_code": modified_code,
            "diff": diff_result.get("diff", ""),
            "explanation": response,
            "error": write_result.get("error")
        }
    
    def debug_code(
        self,
        file_path: str,
        error_description: str = None,
        error_output: str = None
    ) -> Dict[str, Any]:
        """
        Debug code based on error description or output.
        
        Args:
            file_path: Path to the file to debug
            error_description: Description of the error
            error_output: Error output from running the code
            
        Returns:
            Dictionary with debugging results
        """
        # Read the existing code
        file_result = self.tools.read_file(file_path)
        
        if not file_result["success"]:
            return {
                "success": False,
                "error": file_result["error"]
            }
        
        code = file_result["content"]
        
        # Get the file extension and determine the language
        _, ext = os.path.splitext(file_path)
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.rb': 'ruby'
        }
        language = language_map.get(ext, 'python')
        
        prompt = f"""
        Debug the following {language} code:
        
        ```{language}
        {code}
        ```
        """
        
        if error_description:
            prompt += f"""
            Error description:
            {error_description}
            """
        
        if error_output:
            prompt += f"""
            Error output:
            ```
            {error_output}
            ```
            """
        
        prompt += """
        Please:
        1. Identify the bugs or issues in the code
        2. Explain the root cause of each issue
        3. Provide a fixed version of the code
        4. Explain your fixes and how they address the problems
        """
        
        response = self.agent.run(prompt)
        
        # Extract code from the response
        code_lines = []
        in_code_block = False
        
        for line in response.split('\n'):
            if line.startswith('```') and language in line:
                in_code_block = True
                continue
            elif line.startswith('```') and in_code_block:
                in_code_block = False
                continue
            
            if in_code_block:
                code_lines.append(line)
        
        fixed_code = '\n'.join(code_lines)
        
        # Get the diff
        diff_result = self.tools.get_diff(code, fixed_code)
        
        return {
            "success": True,
            "original_code": code,
            "fixed_code": fixed_code,
            "diff": diff_result.get("diff", ""),
            "analysis": response
        }
    
    def create_tests(
        self,
        file_path: str,
        test_framework: str = "pytest"
    ) -> Dict[str, Any]:
        """
        Create tests for the code in the specified file.
        
        Args:
            file_path: Path to the file to test
            test_framework: Testing framework to use
            
        Returns:
            Dictionary with test creation results
        """
        # Read the existing code
        file_result = self.tools.read_file(file_path)
        
        if not file_result["success"]:
            return {
                "success": False,
                "error": file_result["error"]
            }
        
        code = file_result["content"]
        
        # Determine the test file path
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        file_base, _ = os.path.splitext(file_name)
        test_file = os.path.join(file_dir, f"test_{file_base}.py")
        
        prompt = f"""
        Create tests for the following Python code using {test_framework}:
        
        ```python
        {code}
        ```
        
        Please create comprehensive tests that:
        1. Test normal functionality
        2. Test edge cases
        3. Test error conditions
        4. Achieve good code coverage
        
        Include appropriate setup and teardown logic if needed.
        """
        
        response = self.agent.run(prompt)
        
        # Extract code from the response
        code_lines = []
        in_code_block = False
        
        for line in response.split('\n'):
            if line.startswith('```') and ('python' in line or test_framework.lower() in line):
                in_code_block = True
                continue
            elif line.startswith('```') and in_code_block:
                in_code_block = False
                continue
            
            if in_code_block:
                code_lines.append(line)
        
        test_code = '\n'.join(code_lines)
        
        # Write the test code to the file
        write_result = self.tools.write_file(test_file, test_code)
        
        return {
            "success": write_result["success"],
            "test_code": test_code,
            "test_file": test_file,
            "explanation": response,
            "error": write_result.get("error")
        }
    
    def run_project_tests(
        self,
        project_dir: str,
        test_framework: str = "pytest"
    ) -> Dict[str, Any]:
        """
        Run tests for an entire project.
        
        Args:
            project_dir: Directory containing the project
            test_framework: Testing framework to use
            
        Returns:
            Dictionary with test results
        """
        if test_framework == "pytest":
            command = "python -m pytest"
        elif test_framework == "unittest":
            command = "python -m unittest discover"
        else:
            return {
                "success": False,
                "error": f"Unsupported test framework: {test_framework}"
            }
        
        result = self.tools.run_command(command, cwd=project_dir)
        
        return {
            "success": result["success"],
            "output": result["stdout"],
            "errors": result["stderr"],
            "returncode": result["returncode"]
        }
    
    def search_code(
        self,
        project_dir: str,
        query: str,
        file_pattern: str = None
    ) -> Dict[str, Any]:
        """
        Search for code matching a query in the project.
        
        Args:
            project_dir: Directory to search
            query: Search query
            file_pattern: Pattern to filter files
            
        Returns:
            Dictionary with search results
        """
        # This would be better implemented with grep or a code search tool
        # but for simplicity, we'll use a basic approach
        
        matches = []
        
        # Get all the files
        for root, _, files in os.walk(project_dir):
            for file in files:
                # Skip non-text files and files not matching the pattern
                if file_pattern and file_pattern not in file:
                    continue
                
                # Skip binary and non-text files
                if file.endswith(('.pyc', '.pyo', '.so', '.o', '.a', '.lib', '.dll', 
                                '.exe', '.bin', '.dat', '.db', '.sqlite', '.jpg', 
                                '.jpeg', '.png', '.gif', '.mp3', '.mp4', '.zip', 
                                '.tar', '.gz')):
                    continue
                
                file_path = os.path.join(root, file)
                
                try:
                    # Read the file and search for the query
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                    
                    if query in content:
                        # Get the lines containing the query
                        lines = content.split('\n')
                        line_matches = []
                        
                        for i, line in enumerate(lines):
                            if query in line:
                                line_matches.append({
                                    "line_number": i + 1,
                                    "line": line.strip()
                                })
                        
                        matches.append({
                            "file": file_path,
                            "line_matches": line_matches
                        })
                except:
                    # Skip files that can't be read
                    continue
        
        return {
            "success": True,
            "matches": matches,
            "query": query
        }

# Example usage
if __name__ == "__main__":
    # Create a coder bot instance
    coder = CoderBot()
    
    # Generate a simple Python function
    result = coder.generate_code(
        description="Create a function that calculates the Fibonacci sequence up to n terms",
        language="python",
        file_path="fibonacci.py"
    )
    
    print("Generated Code:")
    print(result["code"])
    
    # Create tests for the function
    test_result = coder.create_tests(
        file_path="fibonacci.py",
        test_framework="pytest"
    )
    
    print("\nGenerated Tests:")
    print(test_result["test_code"])
    
    # Run the tests
    run_result = coder.run_project_tests(
        project_dir=".",
        test_framework="pytest"
    )
    
    print("\nTest Results:")
    print(run_result["output"])
