#!/usr/bin/env python3
"""
Test script for Claude API integration.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project path to import the Claude API module
sys.path.append(str(Path(__file__).parents[3] / "cookbook" / "coding_agents" / "advanced_bot" / "utils"))
from claude_api import ClaudeAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_sequential_thinking():
    """Test the sequential thinking functionality with Claude API."""
    try:
        # Initialize the Claude API client
        logger.info("Initializing Claude API client...")
        claude = ClaudeAPI()
        
        # Test basic completion first
        logger.info("Testing basic completion...")
        response = claude.complete(
            prompt="What is the sum of 5 and 7?",
            max_tokens=100
        )
        logger.info("Basic completion response:")
        logger.info(json.dumps(response, indent=2))
        
        # Test sequential thinking
        logger.info("Testing sequential thinking...")
        thinking_result = claude.sequential_thinking(
            prompt="How would you approach solving a simple linear equation like 2x + 3 = 7?",
            total_thoughts=3
        )
        logger.info("Sequential thinking result:")
        logger.info(json.dumps(thinking_result, indent=2))
        
        return True
    except Exception as e:
        logger.error(f"Error during API test: {e}", exc_info=True)
        return False

def test_code_generation():
    """Test the code generation functionality with Claude API."""
    try:
        # Initialize the Claude API client
        logger.info("Initializing Claude API client...")
        claude = ClaudeAPI()
        
        # Test code generation
        logger.info("Testing code generation...")
        prompt = "Write a Python function to calculate the Fibonacci sequence up to n terms."
        
        system_prompt = """
You are an expert programmer with deep expertise in software development.
Your task is to generate clean, well-documented, efficient code based on the provided request.
Focus on best practices, readability, and maintainability.
Generate ONLY the code, with appropriate comments to explain the implementation.
"""
        
        response = claude.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1000
        )
        
        # Extract code from response
        generated_code = ""
        if "content" in response and isinstance(response["content"], list):
            for item in response["content"]:
                if item.get("type") == "text":
                    generated_code += item.get("text", "")
        else:
            # Fallback for different response structure
            generated_code = str(response.get("content", ""))
        
        logger.info("Generated code:")
        logger.info(generated_code[:500] + "..." if len(generated_code) > 500 else generated_code)
        
        return True
    except Exception as e:
        logger.error(f"Error during API test: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    # Run the tests
    logger.info("Running Claude API tests...")
    
    success_thinking = test_sequential_thinking()
    if success_thinking:
        logger.info("Sequential thinking test completed successfully!")
    else:
        logger.error("Sequential thinking test failed!")
    
    success_code = test_code_generation()
    if success_code:
        logger.info("Code generation test completed successfully!")
    else:
        logger.error("Code generation test failed!")
    
    # Overall status
    if success_thinking and success_code:
        logger.info("All Claude API tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("Some Claude API tests failed!")
        sys.exit(1)
