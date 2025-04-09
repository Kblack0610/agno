"""
State Manager Module

This module provides state management capabilities for the multi-agent system,
allowing agents to share and persist state information across workflow executions.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from threading import Lock

class StateManager:
    """
    Manages workflow state for the multi-agent system.
    
    Features:
    - Centralized state storage
    - State persistence
    - Thread-safe state updates
    - State history tracking
    - State namespaces for different contexts
    """
    
    def __init__(self, state_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the state manager.
        
        Args:
            state_dir: Directory for persisting state (optional)
        """
        self.logger = logging.getLogger('core.state_manager')
        
        # Main state storage by namespace
        self.state: Dict[str, Dict[str, Any]] = {
            'global': {},
            'workflow': {},
            'agents': {},
            'tasks': {}
        }
        
        # State history tracking
        self.history: Dict[str, List[Dict[str, Any]]] = {
            namespace: [] for namespace in self.state
        }
        
        # Thread safety
        self.state_lock = Lock()
        
        # Persistence settings
        self.state_dir = Path(state_dir) if state_dir else None
        if self.state_dir:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"State will be persisted to: {self.state_dir}")
        
        self.logger.info("State manager initialized")
    
    def get(
            self,
            key: str,
            namespace: str = 'global',
            default: Any = None
        ) -> Any:
        """
        Get a value from the state.
        
        Args:
            key: Key to retrieve
            namespace: State namespace
            default: Default value if key doesn't exist
            
        Returns:
            Value from state or default if not found
        """
        with self.state_lock:
            if namespace not in self.state:
                return default
            
            return self.state[namespace].get(key, default)
    
    def set(
            self,
            key: str,
            value: Any,
            namespace: str = 'global',
            persist: bool = False,
            track_history: bool = True
        ) -> None:
        """
        Set a value in the state.
        
        Args:
            key: Key to set
            value: Value to store
            namespace: State namespace
            persist: Whether to persist state to disk
            track_history: Whether to track change in history
        """
        with self.state_lock:
            # Create namespace if it doesn't exist
            if namespace not in self.state:
                self.state[namespace] = {}
                self.history[namespace] = []
            
            # Track history if requested
            if track_history:
                timestamp = time.time()
                old_value = self.state[namespace].get(key)
                
                self.history[namespace].append({
                    'key': key,
                    'old_value': old_value,
                    'new_value': value,
                    'timestamp': timestamp
                })
                
                # Limit history size
                if len(self.history[namespace]) > 100:
                    self.history[namespace].pop(0)
            
            # Update state
            self.state[namespace][key] = value
            self.logger.debug(f"Set {namespace}.{key} = {value}")
            
            # Persist if requested
            if persist and self.state_dir:
                self._persist_namespace(namespace)
    
    def update(
            self,
            updates: Dict[str, Any],
            namespace: str = 'global',
            persist: bool = False,
            track_history: bool = True
        ) -> None:
        """
        Update multiple values in the state.
        
        Args:
            updates: Dictionary of key-value pairs to update
            namespace: State namespace
            persist: Whether to persist state to disk
            track_history: Whether to track changes in history
        """
        # Acquire lock with timeout protection to prevent deadlocks
        lock_acquired = self.state_lock.acquire(timeout=5)  # 5 second timeout
        
        if not lock_acquired:
            self.logger.error("Failed to acquire state lock for update operation (timeout)")
            return
        
        try:
            # Create namespace if it doesn't exist
            if namespace not in self.state:
                self.state[namespace] = {}
                self.history[namespace] = []
            
            for key, value in updates.items():
                # Track history if requested (directly in update to avoid nested locks)
                if track_history:
                    timestamp = time.time()
                    old_value = self.state[namespace].get(key)
                    
                    self.history[namespace].append({
                        'key': key,
                        'old_value': old_value,
                        'new_value': value,
                        'timestamp': timestamp
                    })
                    
                    # Limit history size
                    if len(self.history[namespace]) > 100:
                        self.history[namespace].pop(0)
                
                # Update state directly
                self.state[namespace][key] = value
                self.logger.debug(f"Set {namespace}.{key} = {value}")
            
            # Persist at the end if requested
            if persist and self.state_dir:
                self._persist_namespace(namespace)
        
        except Exception as e:
            self.logger.error(f"Error during state update: {e}")
            raise
        
        finally:
            # Always release the lock
            self.state_lock.release()
    
    def delete(
            self,
            key: str,
            namespace: str = 'global',
            persist: bool = False,
            track_history: bool = True
        ) -> None:
        """
        Delete a key from the state.
        
        Args:
            key: Key to delete
            namespace: State namespace
            persist: Whether to persist state to disk
            track_history: Whether to track deletion in history
        """
        with self.state_lock:
            if namespace not in self.state:
                return
            
            # Track history if requested
            if track_history and key in self.state[namespace]:
                timestamp = time.time()
                old_value = self.state[namespace].get(key)
                
                self.history[namespace].append({
                    'key': key,
                    'old_value': old_value,
                    'new_value': None,
                    'operation': 'delete',
                    'timestamp': timestamp
                })
            
            # Remove key
            if key in self.state[namespace]:
                del self.state[namespace][key]
                self.logger.debug(f"Deleted {namespace}.{key}")
            
            # Persist if requested
            if persist and self.state_dir:
                self._persist_namespace(namespace)
    
    def get_namespace(self, namespace: str) -> Dict[str, Any]:
        """
        Get all values in a namespace.
        
        Args:
            namespace: State namespace
            
        Returns:
            Copy of the namespace state dictionary
        """
        with self.state_lock:
            if namespace not in self.state:
                return {}
            
            return self.state[namespace].copy()
    
    def get_history(
            self,
            namespace: str = 'global',
            key: Optional[str] = None,
            limit: int = 10
        ) -> List[Dict[str, Any]]:
        """
        Get state change history.
        
        Args:
            namespace: State namespace
            key: Optional key to filter history
            limit: Maximum number of history entries to return
            
        Returns:
            List of history entries, newest first
        """
        with self.state_lock:
            if namespace not in self.history:
                return []
            
            # Filter by key if provided
            if key:
                filtered = [
                    entry for entry in self.history[namespace]
                    if entry['key'] == key
                ]
            else:
                filtered = self.history[namespace]
            
            # Return newest entries first, limited by limit
            return sorted(
                filtered,
                key=lambda x: x['timestamp'],
                reverse=True
            )[:limit]
    
    def reset_namespace(
            self,
            namespace: str,
            persist: bool = False
        ) -> None:
        """
        Reset a namespace to empty state.
        
        Args:
            namespace: State namespace to reset
            persist: Whether to persist state to disk
        """
        with self.state_lock:
            if namespace in self.state:
                # Track complete reset in history
                if namespace in self.history:
                    timestamp = time.time()
                    old_state = self.state[namespace].copy()
                    
                    self.history[namespace].append({
                        'operation': 'reset_namespace',
                        'old_state': old_state,
                        'timestamp': timestamp
                    })
                
                # Reset the namespace
                self.state[namespace] = {}
                self.logger.info(f"Reset namespace: {namespace}")
                
                # Persist if requested
                if persist and self.state_dir:
                    self._persist_namespace(namespace)
    
    def reset_all(self, persist: bool = False) -> None:
        """
        Reset all state namespaces.
        
        Args:
            persist: Whether to persist state to disk
        """
        for namespace in list(self.state.keys()):
            self.reset_namespace(namespace, persist=persist)
        
        self.logger.info("Reset all state namespaces")
    
    def _persist_namespace(self, namespace: str) -> None:
        """
        Persist a namespace to disk.
        
        Args:
            namespace: State namespace to persist
        """
        if not self.state_dir:
            return
        
        try:
            file_path = self.state_dir / f"{namespace}_state.json"
            with open(file_path, 'w') as f:
                json.dump(self.state[namespace], f, indent=2)
            
            self.logger.debug(f"Persisted {namespace} state to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to persist {namespace} state: {e}")
    
    def load_namespace(self, namespace: str) -> bool:
        """
        Load a namespace from disk.
        
        Args:
            namespace: State namespace to load
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.state_dir:
            return False
        
        file_path = self.state_dir / f"{namespace}_state.json"
        if not file_path.exists():
            self.logger.debug(f"No persisted state found for {namespace}")
            return False
        
        try:
            with open(file_path, 'r') as f:
                loaded_state = json.load(f)
            
            with self.state_lock:
                self.state[namespace] = loaded_state
                # Reset history for this namespace
                self.history[namespace] = []
            
            self.logger.info(f"Loaded {namespace} state from {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load {namespace} state: {e}")
            return False
    
    def load_all(self) -> Dict[str, bool]:
        """
        Load all persisted namespaces from disk.
        
        Returns:
            Dictionary of {namespace: success} indicating load results
        """
        if not self.state_dir:
            return {}
        
        results = {}
        
        # Find all state files
        for file_path in self.state_dir.glob("*_state.json"):
            namespace = file_path.stem.replace("_state", "")
            results[namespace] = self.load_namespace(namespace)
        
        return results


# Global instance for singleton access
_global_state_manager = None

def get_state_manager(state_dir: Optional[Union[str, Path]] = None) -> StateManager:
    """
    Get the global state manager instance.
    
    Args:
        state_dir: Directory for persisting state (used only on first call)
        
    Returns:
        Global StateManager instance
    """
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = StateManager(state_dir)
    return _global_state_manager

def reset_state_manager() -> None:
    """
    Reset the global state manager instance.
    
    This is useful for testing and for starting fresh in new sessions.
    """
    global _global_state_manager
    _global_state_manager = None
    logging.getLogger('core.state_manager').info("State manager reset")
