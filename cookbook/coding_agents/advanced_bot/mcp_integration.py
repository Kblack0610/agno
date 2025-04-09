#!/usr/bin/env python3
"""
MCP Integration Module

This module provides integration with the real MCP server for sequential thinking
capabilities. It can be used alongside or as an alternative to the mock implementation.
"""

import os
import sys
import json
import logging
import requests
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MCPIntegration:
    """
    Integration with the real MCP server.
    """
    
    def __init__(self, server_url=None, api_key=None):
        """
        Initialize MCP integration.
        
        Args:
            server_url: URL of the MCP server
            api_key: API key for the MCP server
        """
        self.server_url = server_url or os.environ.get("MCP_SERVER_URL", "http://localhost:5000")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("No API key provided for MCP integration")
        
        logger.info(f"Initialized MCP integration with server: {self.server_url}")
    
    def is_available(self) -> bool:
        """
        Check if the MCP server is available.
        
        Returns:
            True if the server is available, False otherwise
        """
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"MCP server not available: {e}")
            return False
    
    def sequential_thinking(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        next_thought_needed: bool = True,
        is_revision: bool = False,
        revises_thought: int = None,
        branch_from_thought: int = None,
        branch_id: str = None,
        needs_more_thoughts: bool = False
    ) -> Dict[str, Any]:
        """
        Call the sequential thinking capability of the MCP server.
        
        Args:
            thought: Current thought
            thought_number: Current thought number
            total_thoughts: Total expected thoughts
            next_thought_needed: Whether another thought is needed
            is_revision: Whether this thought revises a previous one
            revises_thought: Number of the thought being revised
            branch_from_thought: Thought number to branch from
            branch_id: ID of the branch
            needs_more_thoughts: Whether more thoughts are needed
            
        Returns:
            Dictionary with the next thought
        """
        if not self.is_available():
            logger.error("MCP server not available for sequential thinking")
            raise ConnectionError("MCP server not available")
        
        # Prepare request payload
        payload = {
            "thought": thought,
            "thoughtNumber": thought_number,
            "totalThoughts": total_thoughts,
            "nextThoughtNeeded": next_thought_needed,
            "isRevision": is_revision
        }
        
        # Add optional parameters if provided
        if revises_thought is not None:
            payload["revisesThought"] = revises_thought
        
        if branch_from_thought is not None:
            payload["branchFromThought"] = branch_from_thought
        
        if branch_id is not None:
            payload["branchId"] = branch_id
        
        if needs_more_thoughts:
            payload["needsMoreThoughts"] = needs_more_thoughts
        
        # Add API key if available
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            # Call the MCP server
            response = requests.post(
                f"{self.server_url}/mcp2/sequentialthinking",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Check response
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error calling MCP server: {response.status_code} {response.text}")
                raise Exception(f"Error calling MCP server: {response.status_code}")
        except Exception as e:
            logger.error(f"Error calling MCP server: {e}")
            raise


# Adapter function to match the MCP interface expected by the validation bot
def mcp2_sequentialthinking(
    thought: str,
    thoughtNumber: int,
    totalThoughts: int,
    nextThoughtNeeded: bool = True,
    isRevision: bool = False,
    revisesThought: int = None,
    branchFromThought: int = None,
    branchId: str = None,
    needsMoreThoughts: bool = False
) -> Dict[str, Any]:
    """
    Adapter function for the real MCP server.
    
    Args:
        thought: Current thought
        thoughtNumber: Current thought number
        totalThoughts: Total expected thoughts
        nextThoughtNeeded: Whether another thought is needed
        isRevision: Whether this thought revises a previous one
        revisesThought: Number of the thought being revised
        branchFromThought: Thought number to branch from
        branchId: ID of the branch
        needsMoreThoughts: Whether more thoughts are needed
        
    Returns:
        Dictionary with the next thought
    """
    # Initialize MCP integration
    mcp = MCPIntegration()
    
    # Call the sequential thinking function
    try:
        return mcp.sequential_thinking(
            thought=thought,
            thought_number=thoughtNumber,
            total_thoughts=totalThoughts,
            next_thought_needed=nextThoughtNeeded,
            is_revision=isRevision,
            revises_thought=revisesThought,
            branch_from_thought=branchFromThought,
            branch_id=branchId,
            needs_more_thoughts=needsMoreThoughts
        )
    except Exception as e:
        logger.error(f"Error using real MCP, falling back to mock: {e}")
        
        # Import mock implementation for fallback
        from mock_mcp import mcp2_sequentialthinking as mock_sequentialthinking
        
        logger.info("Falling back to mock MCP implementation")
        return mock_sequentialthinking(
            thought=thought,
            thoughtNumber=thoughtNumber,
            totalThoughts=totalThoughts,
            nextThoughtNeeded=nextThoughtNeeded,
            isRevision=isRevision,
            revisesThought=revisesThought,
            branchFromThought=branchFromThought,
            branchId=branchId,
            needsMoreThoughts=needsMoreThoughts
        )


def test_mcp_connection():
    """Test the connection to the MCP server."""
    mcp = MCPIntegration()
    
    print(f"Testing connection to MCP server at {mcp.server_url}")
    
    if mcp.is_available():
        print("✅ MCP server is available")
        
        # Try a simple sequential thinking request
        try:
            response = mcp.sequential_thinking(
                thought="Testing MCP connection with a simple thought.",
                thought_number=1,
                total_thoughts=2,
                next_thought_needed=True
            )
            
            print(f"✅ Successfully called sequential thinking")
            print(f"Response: {response}")
            
            return True
        except Exception as e:
            print(f"❌ Error calling sequential thinking: {e}")
            return False
    else:
        print("❌ MCP server is not available")
        return False


if __name__ == "__main__":
    # Test MCP connection
    test_mcp_connection()
