
"""Code Review Agent - An agent that reviews code changes and suggests improvements

Install dependencies: `pip install agno difflib`
"""

from textwrap import dedent
from pathlib import Path
import subprocess
import difflib
import os

from agno.agent import Agent
from agno.models.openai import OpenAIChat

class CodeReviewTools:
    def get_diff(self, old_file, new_file):
        """Get the diff between two files"""
        try:
            with open(old_file, 'r') as f1, open(new_file, 'r') as f2:
                old_lines = f1.readlines()
                new_lines = f2.readlines()
            
            diff = difflib.unified_diff(old_lines, new_lines, fromfile=old_file, tofile=new_file)
            return ''.join(diff)
        except Exception as e:
            return f"Error generating diff: {str(e)}"
    
    def get_file_content(self, file_path):
        """Get the content of a file"""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def run_git_diff(self, file_path):
        """Run git diff on a file"""
        try:
            result = subprocess.run(["git", "diff", file_path], capture_output=True, text=True)
            if result.stdout:
                return result.stdout
            else:
                return "No changes detected in git"
        except Exception as e:
            return f"Error running git diff: {str(e)}"
    
    def get_git_blame(self, file_path):
        """Get git blame information for a file"""
        try:
            result = subprocess.run(["git", "blame", file_path], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            return f"Error running git blame: {str(e)}"
    
    def suggest_code_improvements(self, code_content):
        """This is just a placeholder - the agent itself will provide the suggestions
        based on its model and instructions"""
        # The agent will use its LLM to generate improvements
        return "The agent will analyze the code and provide improvements."

code_review_agent = Agent(
    name="Code Review Agent",
    model=OpenAIChat(id="gpt-4o"),
    description="An agent that reviews code changes and suggests improvements",
    instructions=dedent("""\
        You are a Code Review Agent that analyzes code changes and suggests improvements.
        
        Your responsibilities include:
        1. Reviewing code changes for potential issues
        2. Suggesting improvements in code style, performance, and readability
        3. Identifying potential bugs or security vulnerabilities
        4. Providing constructive feedback with examples
        
        When reviewing code, follow these guidelines:
        - Focus on code quality, maintainability, and best practices
        - Check for common issues like:
          * Unused imports or variables
          * Complex or confusing logic
          * Missing error handling
          * Performance bottlenecks
          * Security vulnerabilities
          * Lack of documentation or comments
          * Inconsistent naming or style
        - Suggest specific improvements with code examples
        - Be thorough but prioritize important issues
        - Consider the context of the changes
        - Provide both positive feedback and areas for improvement
        
        Format your reviews with:
        - A summary of the changes or the code being reviewed
        - Positive aspects of the code (what was done well)
        - Suggested improvements with code examples
        - Any potential bugs or issues
        - Overall assessment and recommendations
    """),
    tools=[CodeReviewTools()],
    show_tool_calls=True,
    markdown=True,
)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Code review agent')
    parser.add_argument('file', type=str, help='File to review')
    parser.add_argument('--diff-with', type=str, help='Compare with another file')
    parser.add_argument('--git-diff', action='store_true', help='Use git diff for comparison')
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} does not exist")
        exit(1)
    
    if args.diff_with and not os.path.exists(args.diff_with):
        print(f"Error: Comparison file {args.diff_with} does not exist")
        exit(1)
    
    # Get file content
    file_content = code_review_agent.tools.get_file_content(args.file)
    
    # Prepare prompt based on arguments
    if args.diff_with:
        diff = code_review_agent.tools.get_diff(args.diff_with, args.file)
        prompt = f"Review the following code changes between {args.diff_with} and {args.file}:\n\n```diff\n{diff}\n```\n\nThe current file content is:\n\n```\n{file_content}\n```"
    elif args.git_diff:
        diff = code_review_agent.tools.run_git_diff(args.file)
        prompt = f"Review the following git changes for {args.file}:\n\n```diff\n{diff}\n```\n\nThe current file content is:\n\n```\n{file_content}\n```"
    else:
        prompt = f"Review the following code file {args.file}:\n\n```\n{file_content}\n```"
    
    # Run the agent
    print(f"\nReviewing {args.file}...")
    response = code_review_agent.run(prompt)
    print("\nCode Review Results:")
    print(response)
