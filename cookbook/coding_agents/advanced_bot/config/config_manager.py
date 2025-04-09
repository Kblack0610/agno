"""
Configuration Manager for Advanced Validation Bot.

This module provides a central configuration manager that supports:
- YAML configuration files
- JSON configuration files
- Environment variable overrides
- Default configurations
- Validation profiles
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List

# Try to import yaml, but don't fail if it's not available
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .validation_profile import ValidationProfile

# Set up logging
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Configuration manager for the validation bot.
    
    Handles loading, validation, and access to configuration values,
    with support for multiple file formats and environment variables.
    """
    
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        env_prefix: str = "VALBOT_",
        default_profile: str = "standard"
    ):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to a configuration file or directory
            env_prefix: Prefix for environment variables
            default_profile: Default validation profile to use
        """
        self.config_path = config_path
        self.env_prefix = env_prefix
        self.default_profile = default_profile
        self._profile: Optional[ValidationProfile] = None
        
        # Step 1: Start with default configuration
        self._config: Dict[str, Any] = {}
        self._load_defaults()
        logger.debug(f"Loaded default configuration")
        
        # Step 2: Override with configuration from file(s)
        if config_path:
            self._load_from_path(config_path)
            logger.debug(f"Loaded configuration from {config_path}")
        
        # Step 3: Apply environment variable overrides (highest precedence)
        self._apply_env_vars()
        logger.debug(f"Applied environment variable overrides")
        
        # Step 4: Initialize validation profile
        logger.debug(f"Final configuration: {self._config}")
        self._init_profile()
    
    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self._config = {
            "validation": {
                "profile": self.default_profile,
                "test_frameworks": ["pytest", "unittest"],
                "linters": ["flake8", "pylint"],
                "type_checkers": ["mypy"],
                "timeout": 60,
                "report_format": "json"
            },
            "agents": {
                "test_validation": {
                    "enabled": True,
                    "result_analysis": True,
                    "coverage_threshold": 70
                },
                "code_quality": {
                    "enabled": True,
                    "complexity_threshold": 10,
                    "style_check": True
                },
                "performance": {
                    "enabled": False,
                    "benchmark_iterations": 3
                },
                "security": {
                    "enabled": False,
                    "vulnerability_scan": True,
                    "dependency_check": True
                }
            },
            "sequential_thinking": {
                "enabled": True,
                "max_steps": 10,
                "thought_persistence": True
            },
            "logging": {
                "level": "INFO",
                "file": None,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        logger.debug(f"Default configuration loaded: {self._config}")
    
    def _load_from_path(self, config_path: Union[str, Path]) -> None:
        """
        Load configuration from a file or directory.
        
        Args:
            config_path: Path to a configuration file or directory
        """
        # Convert to Path object if necessary
        if isinstance(config_path, str):
            config_path = Path(config_path)
        
        # Check if the path exists
        if not config_path.exists():
            logger.warning(f"Configuration path does not exist: {config_path}")
            return
        
        # Handle directory vs file
        if config_path.is_dir():
            logger.info(f"Loading configuration from directory: {config_path}")
            
            # Find all configuration files
            json_files = sorted(config_path.glob("*.json"))
            yaml_files = []
            if YAML_AVAILABLE:
                yaml_files = sorted(config_path.glob("*.yaml")) + sorted(config_path.glob("*.yml"))
                
            # Load all configuration files in sorted order
            for file_path in sorted(json_files + yaml_files):
                self._load_config_file(file_path, merge=True)
        else:
            # Load single file (replaces current config)
            self._load_config_file(config_path, merge=False)
    
    def _load_config_file(self, file_path: Path, merge: bool = False) -> None:
        """
        Load configuration from a specific file.
        
        Args:
            file_path: Path to a configuration file
            merge: If True, merge with existing config rather than replace
        """
        if not file_path.exists():
            logger.warning(f"Configuration file does not exist: {file_path}")
            return
        
        logger.info(f"Loading configuration from: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix in (".yml", ".yaml"):
                    if not YAML_AVAILABLE:
                        logger.warning("YAML support is not available. Install PyYAML to use YAML configuration files.")
                        return
                    config_data = yaml.safe_load(f)
                    logger.debug(f"Loaded YAML configuration: {config_data}")
                elif file_path.suffix == ".json":
                    config_data = json.load(f)
                    logger.debug(f"Loaded JSON configuration: {config_data}")
                else:
                    logger.warning(f"Unsupported configuration file format: {file_path.suffix}")
                    return
                
                if not isinstance(config_data, dict):
                    logger.warning(f"Invalid configuration format in: {file_path}")
                    return
                
                # Update configuration
                if merge:
                    # Deep merge with existing configuration
                    self._deep_merge(self._config, config_data)
                    logger.debug(f"Configuration after merge: {self._config}")
                else:
                    # Replace the configuration
                    self._config = config_data
                    logger.debug(f"Configuration updated to: {self._config}")
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep merge two dictionaries, updating the target.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                self._deep_merge(target[key], value)
            else:
                # Replace or add value
                target[key] = value
    
    def _apply_env_vars(self) -> None:
        """
        Apply environment variable overrides.
        
        Environment variables with the configured prefix will override
        configuration values. For example, VALBOT_VALIDATION_PROFILE
        would override validation.profile.
        """
        logger.info(f"Applying environment variable overrides with prefix: {self.env_prefix}")
        
        # Collect overrides from environment variables
        overrides = {}
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Extract configuration key (e.g., VALBOT_VALIDATION_PROFILE -> validation.profile)
                env_key = key[len(self.env_prefix):]
                
                # Special handling for AGENTS_TEST_VALIDATION_ENABLED
                if env_key == "AGENTS_TEST_VALIDATION_ENABLED":
                    config_key = "agents.test_validation.enabled"
                else:
                    # Standard conversion from UPPER_SNAKE_CASE to dot.notation
                    config_key = env_key.lower().replace("_", ".")
                
                typed_value = self._convert_value(value)
                overrides[config_key] = typed_value
                logger.debug(f"Found environment override: {key} -> {config_key} = {typed_value} ({type(typed_value).__name__})")
        
        # Apply all overrides
        for key, value in overrides.items():
            # Split the key into path components
            parts = key.split(".")
            
            # Navigate to the correct nested dictionary
            current = self._config
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                elif not isinstance(current[part], dict):
                    # If a non-dict exists at this level, replace it with a dict
                    current[part] = {}
                current = current[part]
            
            # Set the value at the final level
            if parts:
                last_part = parts[-1]
                current[last_part] = value
                logger.debug(f"Applied override: {key} = {value}")
    
    def _convert_value(self, value: str) -> Any:
        """
        Convert string values to appropriate Python types.
        
        Args:
            value: String value to convert
            
        Returns:
            Converted value
        """
        # Can't convert None
        if value is None:
            return None
            
        # Normalize to lowercase for boolean checks
        value_lower = value.lower()
        
        # Boolean values
        if value_lower in ("true", "yes", "on", "1"):
            return True
        if value_lower in ("false", "no", "off", "0"):
            return False
        
        # Try to convert to int
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try to convert to JSON
        if (value.startswith("[") and value.endswith("]")) or (value.startswith("{") and value.endswith("}")):
            try:
                return json.loads(value)
            except ValueError:
                pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, target: Dict[str, Any], keys: List[str], value: Any) -> None:
        """
        Set a nested value in a dictionary.
        
        Args:
            target: Target dictionary
            keys: List of keys to traverse
            value: Value to set
        """
        if not keys:
            return
        
        key = keys[0]
        
        if len(keys) == 1:
            # Set the value at the final key
            target[key] = value
            return
        
        # If the next level doesn't exist or isn't a dict, create it
        if key not in target or not isinstance(target[key], dict):
            target[key] = {}
        
        # Recursive call to set the value at the next level
        self._set_nested_value(target[key], keys[1:], value)
    
    def _init_profile(self) -> None:
        """Initialize the validation profile."""
        profile_name = self.get("validation.profile", self.default_profile)
        self._profile = ValidationProfile(profile_name, self)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (e.g., "validation.profile")
            default: Default value if key is not found
            
        Returns:
            Configuration value
        """
        if not key:
            return default
        
        # Split the key by dot
        keys = key.split('.')
        
        # Start from the root
        value = self._config
        
        # Traverse the configuration tree
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (e.g., "validation.profile")
            value: Value to set
        """
        parts = key.split('.')
        self._set_nested_value(self._config, parts, value)
        
        # Reinitialize profile if we changed the profile
        if key == "validation.profile":
            self._init_profile()
    
    @property
    def profile(self) -> ValidationProfile:
        """Get the current validation profile."""
        if self._profile is None:
            self._init_profile()
        return self._profile
    
    def save(self, file_path: Union[str, Path], format: str = "yaml") -> None:
        """
        Save the current configuration to a file.
        
        Args:
            file_path: Path to save the configuration
            format: Format to save the configuration in (yaml or json)
        """
        path = Path(file_path)
        
        try:
            with open(path, 'w') as f:
                if format.lower() == "yaml":
                    if not YAML_AVAILABLE:
                        logger.warning("YAML support is not available. Using JSON format instead.")
                        json.dump(self._config, f, indent=2)
                    else:
                        yaml.dump(self._config, f, default_flow_style=False)
                else:
                    json.dump(self._config, f, indent=2)
                    
            logger.info(f"Configuration saved to: {path}")
        except Exception as e:
            logger.error(f"Error saving configuration to {path}: {e}")
    
    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using dictionary syntax."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set a configuration value using dictionary syntax."""
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        """Check if a configuration path exists."""
        return self.get(key) is not None
    
    def __str__(self) -> str:
        """Get a string representation of the configuration."""
        if YAML_AVAILABLE:
            return yaml.dump(self._config, default_flow_style=False)
        return json.dumps(self._config, indent=2)

    def load_config(self, config_path: Union[str, Path]) -> None:
        """
        Load configuration from a file or directory.
        
        This is a public method that wraps _load_from_path for backward compatibility.
        
        Args:
            config_path: Path to a configuration file or directory
        """
        # Store the path
        self.config_path = config_path if isinstance(config_path, Path) else Path(config_path)
        
        # Load the configuration
        self._load_from_path(config_path)
        
        # Reinitialize the profile
        self._init_profile()
