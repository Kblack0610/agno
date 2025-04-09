
"""Demonstration of the complete coding agents workflow"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path to import the agents
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from code_testing_agent import code_testing_agent
from code_review_agent import code_review_agent

def demo_workflow():
    """Demonstrate a complete workflow using the coding agents"""
    # Get the path to the example calculator test file
    test_file = Path(__file__).parent / 'test_calculator.py'
    
    if not test_file.exists():
        print(f"Error: Test file {test_file} not found")
        return
    
    print("=" * 80)
    print("CODING AGENTS WORKFLOW DEMONSTRATION")
    print("=" * 80)
    
    # Step 1: Run the code testing agent
    print("\nSTEP 1: Running Code Testing Agent\n")
    print(f"Analyzing {test_file}...")
    
    # Get the file content
    with open(test_file, 'r') as f:
        file_content = f.read()
    
    # Run the code testing agent
    prompt = f"Analyze the following code file: {test_file}\n\n```python\n{file_content}\n```"
    test_result = code_testing_agent.run(prompt)
    
    print("\nCode Testing Results:")
    print("-" * 60)
    print(test_result)
    print("-" * 60)
    
    # Step 2: Make a copy of the file with improvements
    print("\nSTEP 2: Creating improved version of the file\n")
    
    improved_file = test_file.with_stem(test_file.stem + "_improved")
    
    # Create an improved version with the division by zero check
    with open(test_file, 'r') as f:
        improved_content = f.read().replace(
            "    def divide(self, a, b):\n        # Bug: no check for division by zero\n        return a / b",
            "    def divide(self, a, b):\n        # Fixed: added check for division by zero\n        if b == 0:\n            raise ValueError('Cannot divide by zero')\n        return a / b"
        )
    
    with open(improved_file, 'w') as f:
        f.write(improved_content)
    
    print(f"Created improved version at {improved_file}")
    
    # Step 3: Run the code review agent to compare the files
    print("\nSTEP 3: Running Code Review Agent to compare versions\n")
    
    # Compare the original and improved files
    diff_prompt = f"Review the changes between the original and improved calculator implementations. Original file: {test_file}, Improved file: {improved_file}"
    
    print(f"Reviewing changes...")
    diff = code_review_agent.tools.get_diff(str(test_file), str(improved_file))
    review_prompt = f"Review the following code changes:\n\n```diff\n{diff}\n```"
    review_result = code_review_agent.run(review_prompt)
    
    print("\nCode Review Results:")
    print("-" * 60)
    print(review_result)
    print("-" * 60)
    
    print("\nWorkflow demonstration complete!")
    print("In a real scenario, the continuous_monitor.py script would detect these changes automatically.")
    print("=" * 80)

if __name__ == "__main__":
    demo_workflow()
