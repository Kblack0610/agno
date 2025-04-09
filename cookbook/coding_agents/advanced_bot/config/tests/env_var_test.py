"""
Simple test file to isolate and fix the environment variable issue.
"""

import os
import sys
import pprint
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config_manager import ConfigManager

def main():
    """Test environment variable overrides with a simple case."""
    # Start fresh - clear any existing VALBOT env vars
    for key in list(os.environ.keys()):
        if key.startswith("VALBOT_"):
            del os.environ[key]
    
    # Create a configuration manager with defaults
    config = ConfigManager()
    print(f"Default config loaded")
    print(f"agents.test_validation.enabled = {config.get('agents.test_validation.enabled')}")
    
    # Set environment variable directly
    os.environ["VALBOT_AGENTS_TEST_VALIDATION_ENABLED"] = "false"
    print(f"\nSet VALBOT_AGENTS_TEST_VALIDATION_ENABLED to 'false'")
    
    # Debug what's in the environment
    print(f"Environment variable value: {os.environ.get('VALBOT_AGENTS_TEST_VALIDATION_ENABLED')}")
    
    # Create a new config with environment variables
    config2 = ConfigManager(env_prefix="VALBOT_")
    print(f"New config created with environment variables")
    print(f"agents.test_validation.enabled = {config2.get('agents.test_validation.enabled')}")
    
    # Directly checking the raw config
    print("\nRaw config structure:")
    pprint.pprint(config2._config.get('agents', {}))
    
    # Try direct manipulation
    print("\nTrying direct manipulation:")
    config3 = ConfigManager()
    config3._config['agents']['test_validation']['enabled'] = False
    print(f"After direct manipulation: {config3.get('agents.test_validation.enabled')}")
    
    # Cleanup
    del os.environ["VALBOT_AGENTS_TEST_VALIDATION_ENABLED"]
    
if __name__ == "__main__":
    main()
