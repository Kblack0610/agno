
"""Code Testing Agent - An agent that performs continuous testing and validation of code

Install dependencies: `pip install agno pytest flake8 mypy`
"""

from textwrap import dedent
from pathlib import Path
import subprocess
import os
import time

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage

# Custom tools for code testing
class CodeTestingTools:
    def run_tests(self, directory, test_pattern="test_*.py"):
        """Run tests in the specified directory"""
        result = subprocess.run(["pytest", directory, "-v"], capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "errors": result.stderr
        }
    
    def lint_code(self, file_path):
        """Lint code with flake8"""
        result = subprocess.run(["flake8", file_path], capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "issues": result.stdout
        }
    
    def check_typing(self, file_path):
        """Check type hints with mypy"""
        result = subprocess.run(["mypy", file_path], capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "issues": result.stdout
        }
    
    def get_file_content(self, file_path):
        """Get the content of a file"""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"

# Setup paths and storage
cwd = Path(__file__).parent
tmp_dir = cwd.joinpath("tmp")
tmp_dir.mkdir(parents=True, exist_ok=True)

agent_storage = SqliteStorage(
    table_name="code_testing_sessions",
    db_file=str(tmp_dir.joinpath("code_testing_sessions.db")),
)

code_testing_agent = Agent(
    name="Code Testing Agent",
    model=OpenAIChat(id="gpt-4o"),
    description="An agent that performs continuous testing and validation of code",
    instructions=dedent("""\
        You are a Code Testing Agent that continuously validates code quality and correctness.
        
        Your responsibilities include:
        1. Running tests when code changes are detected
        2. Performing static code analysis for quality issues
        3. Checking type consistency with mypy
        4. Reporting issues in a structured format
        5. Suggesting improvements to fix identified issues
        
        When analyzing code, follow these guidelines:
        - Prioritize test failures over lint issues
        - Group related issues together
        - Provide specific recommendations for fixing issues
        - Include code examples where appropriate
        - Track recurring issues to identify patterns
        
        Format your reports with:
        - A clear summary of findings
        - Test results (passed/failed)
        - Code quality issues categorized by severity
        - Suggested improvements with code samples
        - Next steps for developers
    """),
    tools=[CodeTestingTools()],
    storage=agent_storage,
    show_tool_calls=True,
    add_history_to_messages=True,
    num_history_responses=5,
    markdown=True,
)

if __name__ == "__main__":
    # Example usage
    file_to_analyze = input("Enter path to file to analyze (or press Enter for demo): ")
    
    if not file_to_analyze:
        # Create a demo file with issues
        demo_file = tmp_dir.joinpath("demo_test.py")
        with open(demo_file, "w") as f:
            f.write("""
import unittest

class TestMath(unittest.TestCase):
    def test_addition(self):
        # This test will pass
        result = 1 + 1
        self.assertEqual(result, 2)
    
    def test_subtraction(self):
        # This test will fail
        result = 5 - 2
        self.assertEqual(result, 2)  # Should be 3

if __name__ == "__main__":
    unittest.main()
""")
        file_to_analyze = str(demo_file)
    
    # Run the agent to analyze the file
    print(f"Analyzing {file_to_analyze}...")
    response = code_testing_agent.run(f"Analyze the code in {file_to_analyze} for issues")
    print("
Analysis Results:")
    print(response)
