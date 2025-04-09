
"""
Mock Sequential Orchestrator for testing purposes

This provides a simplified version of the SequentialOrchestrator class for testing
"""

import json
import time
from typing import Dict, List, Any, Optional, Union

class SequentialOrchestrator:
    """Mock version of the SequentialOrchestrator class for testing purposes"""
    
    def __init__(self):
        """Initialize the sequential orchestrator."""
        self.current_chain_id = None
        self.chains = {}
    
    def start_validation_chain(
            self,
            prompt: str,
            validation_type: str,
            estimated_steps: int = 5
        ) -> Dict[str, Any]:
        """
        Start a new validation chain.
        
        Args:
            prompt: Prompt for the validation
            validation_type: Type of validation
            estimated_steps: Estimated number of steps
            
        Returns:
            Chain information
        """
        chain_id = f"chain_{int(time.time())}"
        self.current_chain_id = chain_id
        
        chain = {
            "id": chain_id,
            "status": "initialized",
            "prompt": prompt,
            "validation_type": validation_type,
            "estimated_steps": estimated_steps,
            "current_step": 1,
            "thought_history": [
                {
                    "step": 1,
                    "thought": f"Starting validation chain for {validation_type}",
                    "timestamp": time.time()
                }
            ],
            "validation_results": None
        }
        
        self.chains[chain_id] = chain
        return chain
    
    def continue_validation_chain(
            self,
            next_thought: str
        ) -> Dict[str, Any]:
        """
        Continue an existing validation chain.
        
        Args:
            next_thought: Next thought in the chain
            
        Returns:
            Updated chain information
        """
        if not self.current_chain_id or self.current_chain_id not in self.chains:
            raise ValueError("No active validation chain")
        
        chain = self.chains[self.current_chain_id]
        
        if chain["status"] == "completed":
            raise ValueError("Chain is already completed")
        
        chain["current_step"] += 1
        chain["status"] = "in_progress"
        
        chain["thought_history"].append({
            "step": chain["current_step"],
            "thought": next_thought,
            "timestamp": time.time()
        })
        
        return chain
    
    def complete_validation_chain(
            self,
            final_thought: str,
            validation_results: Dict[str, Any]
        ) -> Dict[str, Any]:
        """
        Complete a validation chain.
        
        Args:
            final_thought: Final thought in the chain
            validation_results: Results of the validation
            
        Returns:
            Completed chain information
        """
        if not self.current_chain_id or self.current_chain_id not in self.chains:
            raise ValueError("No active validation chain")
        
        chain = self.chains[self.current_chain_id]
        
        if chain["status"] == "completed":
            raise ValueError("Chain is already completed")
        
        chain["current_step"] += 1
        chain["status"] = "completed"
        
        chain["thought_history"].append({
            "step": chain["current_step"],
            "thought": final_thought,
            "timestamp": time.time()
        })
        
        chain["validation_results"] = validation_results
        
        return chain
