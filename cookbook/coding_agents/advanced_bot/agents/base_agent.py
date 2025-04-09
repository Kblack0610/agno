"""
Base Agent Module

This module defines the BaseAgent abstract class that all agents in the system
should inherit from, providing common functionality and interfaces.
"""

import abc
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

# Import configuration management
from config.config_manager import ConfigManager

class BaseAgent(abc.ABC):
    """
    Abstract base class for all agents in the multi-agent system.
    
    This class defines the core interface that all agents must implement,
    along with common functionality such as configuration management,
    logging, and basic agent identity.
    """
    
    def __init__(
            self,
            name: str = None,
            agent_id: str = None,
            config_path: Optional[Union[str, Path]] = None,
            verbose: bool = False
        ):
        """
        Initialize the base agent.
        
        Args:
            name: Human-readable name for the agent
            agent_id: Unique identifier for the agent (generated if not provided)
            config_path: Path to configuration file or directory
            verbose: Whether to enable verbose logging
        """
        # Set up agent identity
        self.name = name or self.__class__.__name__
        self.agent_id = agent_id or str(uuid.uuid4())
        
        # Initialize configuration
        self.config = ConfigManager(config_path)
        
        # Set up logging
        self.logger = logging.getLogger(f"agent.{self.name}")
        log_level = logging.DEBUG if verbose else logging.INFO
        self.logger.setLevel(log_level)
        
        # Initialize capabilities and state
        self.capabilities = []
        self.state = {"status": "initialized"}
        
        self.logger.info(f"Agent {self.name} ({self.agent_id}) initialized")
    
    @abc.abstractmethod
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.
        
        This method must be implemented by all agent subclasses.
        
        Args:
            context: Dictionary containing input data and state information
            
        Returns:
            Dictionary with the results of the agent's execution
        """
        pass
    
    def register_capability(self, capability: str) -> None:
        """
        Register a capability that this agent supports.
        
        Args:
            capability: String identifier for the capability
        """
        if capability not in self.capabilities:
            self.capabilities.append(capability)
            self.logger.debug(f"Registered capability: {capability}")
    
    def has_capability(self, capability: str) -> bool:
        """
        Check if the agent has a specific capability.
        
        Args:
            capability: String identifier for the capability
            
        Returns:
            True if the agent has the capability, False otherwise
        """
        return capability in self.capabilities
    
    def update_state(self, state_updates: Dict[str, Any]) -> None:
        """
        Update the agent's internal state.
        
        Args:
            state_updates: Dictionary with state values to update
        """
        self.state.update(state_updates)
        self.logger.debug(f"State updated: {state_updates}")
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the agent.
        
        Returns:
            Dictionary with the agent's current state
        """
        return self.state.copy()
    
    def reset(self) -> None:
        """
        Reset the agent to its initial state.
        """
        self.state = {"status": "initialized"}
        self.logger.info(f"Agent {self.name} reset to initial state")
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} ({self.agent_id})"
