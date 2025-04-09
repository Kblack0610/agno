#!/usr/bin/env python3
"""
Claude API Integration Module

This module provides utilities for interacting with Claude 3.7 API 
for enhanced sequential thinking and other LLM capabilities.
"""

import os
import json
import logging
import requests
import time
import random
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class ClaudeAPI:
    """
    Client for interacting with Claude API endpoints.
    """
    
    def __init__(
            self,
            api_key: Optional[str] = None,
            model: str = "claude-3-7-sonnet-latest",
            base_url: str = "https://api.anthropic.com",
            max_retries: int = 3,
            timeout: int = 90
        ):
        """
        Initialize the Claude API client.
        
        Args:
            api_key: API key for authentication (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use for completions
            base_url: Base URL for API requests
            max_retries: Maximum number of retries for API calls
            timeout: Timeout in seconds for API calls
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in ANTHROPIC_API_KEY environment variable")
        
        self.model = model
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Updated headers for latest Anthropic API
        self.headers = {
            "x-api-key": self.api_key,  # For legacy support
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}"  # New Bearer token authentication
        }
        
        logger.info(f"Initialized Claude API client with model: {model}")

    def complete(
            self, 
            prompt: str, 
            system_prompt: Optional[str] = None, 
            max_tokens: int = 2000, 
            temperature: float = 0.7, 
            stop_sequences: Optional[List[str]] = None
        ) -> Dict[str, Any]:
        """
        Generate a completion response from the Claude API.
        
        Args:
            prompt: The user message to send to the API
            system_prompt: Optional system prompt to guide the model's behavior
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature parameter for controlling randomness
            stop_sequences: Optional list of stop sequences
            
        Returns:
            Dictionary containing the completion response or error information
        """
        # Prepare the request payload
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
            
        # Add stop sequences if provided
        if stop_sequences:
            payload["stop_sequences"] = stop_sequences
            
        logger.debug(f"Sending request to Claude API with payload: {json.dumps(payload)}")
        
        # Make the API request with retry logic
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"API request attempt {attempt + 1}/{max_retries}")
                
                response = requests.post(
                    f"{self.base_url}/v1/messages",
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                # Log response status
                logger.debug(f"API response status: {response.status_code}")
                
                # Check if the request was successful
                if response.status_code == 200:
                    response_data = response.json()
                    logger.debug(f"API response data: {json.dumps(response_data)}")
                    
                    # Extract content from response
                    if "content" in response_data:
                        # Handle list of content blocks
                        if isinstance(response_data["content"], list):
                            content = ""
                            for block in response_data["content"]:
                                if block.get("type") == "text":
                                    content += block.get("text", "")
                        else:
                            content = str(response_data["content"])
                    else:
                        # Try to extract content from new API format
                        content = ""
                        for message in response_data.get("messages", []):
                            if message.get("role") == "assistant":
                                if isinstance(message.get("content"), list):
                                    for block in message.get("content", []):
                                        if block.get("type") == "text":
                                            content += block.get("text", "")
                                else:
                                    content += str(message.get("content", ""))
                        
                    return {
                        "success": True,
                        "content": content,
                        "usage": response_data.get("usage", {})
                    }
                else:
                    # Log detailed error information
                    logger.error(f"API request failed with status {response.status_code}")
                    error_detail = "Unknown error"
                    
                    # Try to extract error details from response
                    try:
                        error_data = response.json()
                        logger.error(f"Error response: {json.dumps(error_data)}")
                        error_detail = error_data.get("error", {}).get("message", "Unknown error")
                    except Exception as e:
                        logger.error(f"Failed to parse error response: {e}")
                        error_detail = response.text[:200] if response.text else "Unknown error"
                    
                    # Check if we should retry
                    if response.status_code in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                        retry_delay_with_jitter = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Retrying in {retry_delay_with_jitter:.2f} seconds...")
                        time.sleep(retry_delay_with_jitter)
                        continue
                    
                    return {
                        "success": False,
                        "error": f"API request failed with status {response.status_code}: {error_detail}"
                    }
                    
            except Exception as e:
                logger.error(f"Exception during API request: {e}", exc_info=True)
                
                # Check if we should retry
                if attempt < max_retries - 1:
                    retry_delay_with_jitter = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Retrying in {retry_delay_with_jitter:.2f} seconds...")
                    time.sleep(retry_delay_with_jitter)
                else:
                    return {
                        "success": False,
                        "error": f"API request failed after {max_retries} attempts: {str(e)}"
                    }
        
        # This should not happen, but just in case
        return {
            "success": False,
            "error": "Failed to get response from API after maximum retries"
        }

    def sequential_thinking(
            self,
            prompt: str,
            context: Optional[Dict[str, Any]] = None,
            total_thoughts: int = 5
        ) -> Dict[str, Any]:
        """
        Generate sequential thinking for a given prompt using Claude.
        
        Args:
            prompt: The problem or task to think about
            context: Additional context for the thinking process
            total_thoughts: Number of thoughts to generate
            
        Returns:
            Dictionary with thinking steps and results
        """
        logger.info(f"Generating sequential thinking for prompt: {prompt[:50]}...")
        
        # Create system prompt for sequential thinking
        system_prompt = """
You are an expert at breaking down complex problems through step-by-step thinking.
Your task is to analyze the given problem and generate a sequence of thoughts that show your reasoning process.
You should:
1. Start by understanding the problem
2. Break it down into sub-problems if needed
3. Analyze each component methodically
4. Identify potential approaches and solutions
5. Evaluate trade-offs between different approaches
6. Reach a final conclusion or plan

Format your response as a numbered list of thoughts, with each thought building on previous ones.
Be thorough and clear in your reasoning. Show your complete thinking process.
"""
        
        # Create the user prompt with context
        user_prompt = f"Problem to analyze: {prompt}\n\n"
        if context:
            user_prompt += f"Additional context:\n{json.dumps(context, indent=2)}\n\n"
        
        user_prompt += f"Please generate {total_thoughts} sequential thoughts that analyze this problem step by step."
        
        # Get the completion
        response = self.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=4000,
            temperature=0.7
        )
        
        # Extract and format the thoughts
        thoughts = []
        
        # The structure of response from /v1/messages is different
        # Look for content in the response structure
        content = None
        if "content" in response:
            content = response["content"]
        elif "message" in response and "content" in response["message"]:
            content = response["message"]["content"]
        
        # Process the content based on its structure
        if content and isinstance(content, list):
            for item in content:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    thoughts.append(text)
        else:
            # Fallback to using the entire response
            thoughts = [str(response)]
        
        # Parse the thoughts into a structured format
        structured_thoughts = []
        thought_text = "\n".join(thoughts)
        
        # Simple parsing for numbered thoughts
        import re
        thought_matches = re.findall(r'(\d+)\.\s+(.*?)(?=\n\d+\.|\Z)', thought_text, re.DOTALL)
        
        for idx, (num, thought) in enumerate(thought_matches, 1):
            structured_thoughts.append({
                "thought": thought.strip(),
                "thoughtNumber": idx,
                "totalThoughts": total_thoughts,
                "nextThoughtNeeded": idx < len(thought_matches)
            })
        
        # If the parsing failed or didn't work as expected, use a simpler approach
        if not structured_thoughts:
            lines = thought_text.split('\n')
            for idx, line in enumerate(lines, 1):
                if line.strip():
                    structured_thoughts.append({
                        "thought": line.strip(),
                        "thoughtNumber": idx,
                        "totalThoughts": total_thoughts,
                        "nextThoughtNeeded": idx < len(lines)
                    })
        
        # Ensure we don't exceed the requested number of thoughts
        structured_thoughts = structured_thoughts[:total_thoughts]
        
        # Format result to match the expected output structure
        result = {
            "success": True,
            "steps": structured_thoughts
        }
        
        logger.info(f"Generated {len(structured_thoughts)} thoughts for prompt: {prompt[:30]}...")
        
        return result

# Example usage
if __name__ == "__main__":
    # Example with environment variable API key
    try:
        claude = ClaudeAPI()
        
        # Test basic completion
        response = claude.complete(
            prompt="Explain the concept of recursion in programming",
            max_tokens=500
        )
        print("Basic completion result:")
        print(response)
        
        # Test sequential thinking
        thinking_result = claude.sequential_thinking(
            prompt="Design a simple command-line calculator application in Python",
            total_thoughts=3
        )
        print("\nSequential thinking result:")
        print(json.dumps(thinking_result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
