"""
Debug test to diagnose environment variable override issues.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config_manager import ConfigManager

def test_env_override():
    """Test environment variable override directly."""
    # Clear any existing environment variables with our prefix
    for key in list(os.environ.keys()):
        if key.startswith("VALBOT_"):
            del os.environ[key]
            
    # Set the environment variable for testing
    os.environ["VALBOT_AGENTS_TEST_VALIDATION_ENABLED"] = "false"
    
    # Create a new config manager
    config = ConfigManager(env_prefix="VALBOT_")
    
    # Check the value directly
    value = config.get("agents.test_validation.enabled")
    print(f"Value type: {type(value)}, Value: {value}")
    
    # Check the raw config dictionary
    full_config = config._config
    if "agents" in full_config and "test_validation" in full_config["agents"]:
        print(f"Raw config value: {full_config['agents']['test_validation']['enabled']}")
    
    # Try setting directly
    config._config["agents"]["test_validation"]["enabled"] = False
    print(f"After direct set: {config.get('agents.test_validation.enabled')}")
    
    # Clean up
    del os.environ["VALBOT_AGENTS_TEST_VALIDATION_ENABLED"]
    
if __name__ == "__main__":
    test_env_override()
