"""
Unit tests for the ConfigManager class.

These tests verify that the configuration manager correctly loads, parses,
and provides access to configuration settings.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile

class TestConfigManager(unittest.TestCase):
    """Tests for the ConfigManager class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up the test environment."""
        self.temp_dir.cleanup()
    
    def test_default_config(self):
        """Test that the default configuration is loaded correctly."""
        config = ConfigManager()
        
        # Check some default values
        self.assertEqual(config.get("validation.profile"), "standard")
        self.assertIn("pytest", config.get("validation.test_frameworks"))
        self.assertEqual(config.get("agents.test_validation.coverage_threshold"), 70)
        self.assertEqual(config.get("logging.level"), "INFO")
    
    def test_json_config_loading(self):
        """Test loading configuration from a JSON file."""
        # Create a test JSON config
        json_config = {
            "validation": {
                "profile": "custom",
                "timeout": 120
            },
            "agents": {
                "test_validation": {
                    "coverage_threshold": 85
                }
            }
        }
        
        json_path = self.config_dir / "test_config.json"
        with open(json_path, 'w') as f:
            json.dump(json_config, f)
        
        # Load the config (create a fresh instance to avoid defaults)
        config = ConfigManager()
        config.load_config(json_path)
        
        # Check that values were correctly loaded
        self.assertEqual(config.get("validation.profile"), "custom")
        self.assertEqual(config.get("validation.timeout"), 120)
        self.assertEqual(config.get("agents.test_validation.coverage_threshold"), 85)
    
    def test_yaml_config_loading(self):
        """Test loading configuration from a YAML file if PyYAML is available."""
        try:
            import yaml
            
            # Create a test YAML config
            yaml_config = """
            validation:
              profile: strict
              timeout: 180
            agents:
              code_quality:
                complexity_threshold: 5
            """
            
            yaml_path = self.config_dir / "test_config.yaml"
            with open(yaml_path, 'w') as f:
                f.write(yaml_config)
            
            # Load the config
            config = ConfigManager()
            config.load_config(yaml_path)
            
            # Check that values were correctly loaded
            self.assertEqual(config.get("validation.profile"), "strict")
            self.assertEqual(config.get("validation.timeout"), 180)
            self.assertEqual(config.get("agents.code_quality.complexity_threshold"), 5)
        except ImportError:
            self.skipTest("PyYAML not installed, skipping YAML test")
    
    def test_env_var_override(self):
        """Test that environment variables override configuration values."""
        # Create a clean environment
        original_env = os.environ.copy()
        
        try:
            # Clear relevant environment variables first
            for key in list(os.environ.keys()):
                if key.startswith("VALBOT_"):
                    del os.environ[key]
            
            # Set environment variables
            os.environ["VALBOT_VALIDATION_PROFILE"] = "minimal"
            os.environ["VALBOT_VALIDATION_TIMEOUT"] = "45"
            # Make sure to use lowercase "false" for better compatibility
            os.environ["VALBOT_AGENTS_TEST_VALIDATION_ENABLED"] = "false"
            
            print("\nDEBUG: Setting VALBOT_AGENTS_TEST_VALIDATION_ENABLED to 'false'")
            print(f"DEBUG: Original env value: {os.environ.get('VALBOT_AGENTS_TEST_VALIDATION_ENABLED')}")
            
            # Create a config with default values first
            config = ConfigManager()
            print(f"DEBUG: Default config value: {config.get('agents.test_validation.enabled')}")
            
            # Create a new config with env vars
            config = ConfigManager(env_prefix="VALBOT_")
            
            # Debug dumps
            print(f"DEBUG: Raw config: {config._config.get('agents', {}).get('test_validation', {})}")
            print(f"DEBUG: Final value: {config.get('agents.test_validation.enabled')}")
            print(f"DEBUG: Value type: {type(config.get('agents.test_validation.enabled'))}")
            
            # Verify that environment variables override defaults
            self.assertEqual(config.get("validation.profile"), "minimal")
            self.assertEqual(config.get("validation.timeout"), 45)  # Should be converted to int
            
            # We know this fails, let's manually assert each level to see where it goes wrong
            agents = config._config.get("agents", {})
            self.assertTrue(isinstance(agents, dict), "agents section is not a dictionary")
            
            test_validation = agents.get("test_validation", {})
            self.assertTrue(isinstance(test_validation, dict), "test_validation section is not a dictionary")
            
            enabled = test_validation.get("enabled", None)
            self.assertEqual(enabled, False, f"enabled should be False, got {enabled} of type {type(enabled)}")
            
            # This is the one that's failing
            self.assertEqual(config.get("agents.test_validation.enabled"), False)
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
    
    def test_set_get_config(self):
        """Test setting and getting configuration values."""
        config = ConfigManager()
        
        # Set some values
        config.set("validation.profile", "strict")
        config.set("agents.security.enabled", True)
        config.set("logging.file", "test.log")
        
        # Check the values were set
        self.assertEqual(config.get("validation.profile"), "strict")
        self.assertEqual(config.get("agents.security.enabled"), True)
        self.assertEqual(config.get("logging.file"), "test.log")
        
        # Test dictionary-style access
        self.assertEqual(config["validation.profile"], "strict")
        
        # Test setting with dictionary-style access
        config["validation.timeout"] = 90
        self.assertEqual(config.get("validation.timeout"), 90)
    
    def test_save_config(self):
        """Test saving configuration to a file."""
        config = ConfigManager()
        
        # Modify some values
        config.set("validation.profile", "custom")
        config.set("agents.performance.enabled", True)
        
        # Save to JSON
        json_path = self.config_dir / "saved_config.json"
        config.save(json_path, format="json")
        
        # Check that the file was created
        self.assertTrue(json_path.exists())
        
        # Load the saved config and verify
        with open(json_path, 'r') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config["validation"]["profile"], "custom")
        self.assertEqual(saved_config["agents"]["performance"]["enabled"], True)
        
        # Try to save to YAML if PyYAML is available
        try:
            import yaml
            
            yaml_path = self.config_dir / "saved_config.yaml"
            config.save(yaml_path, format="yaml")
            
            # Check that the file was created
            self.assertTrue(yaml_path.exists())
        except ImportError:
            pass
    
    def test_directory_config_loading(self):
        """Test loading configuration from a directory with multiple files."""
        # Create multiple config files in a directory
        config_dir = self.config_dir / "multi_config"
        config_dir.mkdir(exist_ok=True)
        
        # Create a base config
        base_config = {
            "validation": {
                "profile": "standard",
                "timeout": 60
            }
        }
        with open(config_dir / "01_base.json", 'w') as f:
            json.dump(base_config, f)
        
        # Create an override config
        override_config = {
            "validation": {
                "timeout": 90
            },
            "agents": {
                "security": {
                    "enabled": True
                }
            }
        }
        with open(config_dir / "02_override.json", 'w') as f:
            json.dump(override_config, f)
        
        # Load configs from the directory
        config = ConfigManager(config_path=config_dir)
        
        # Check that configs were merged correctly with later files taking precedence
        self.assertEqual(config.get("validation.profile"), "standard")  # From base
        self.assertEqual(config.get("validation.timeout"), 90)  # From override
        self.assertEqual(config.get("agents.security.enabled"), True)  # From override
        
        # Try loading a non-existent directory
        config = ConfigManager(config_path=self.config_dir / "nonexistent")
        # Should fall back to defaults
        self.assertEqual(config.get("validation.profile"), "standard")
    
    def test_deep_merge(self):
        """Test the deep merge functionality."""
        config = ConfigManager()
        
        # Create a complex nested dictionary
        config.set("complex.nested.value", 42)
        config.set("complex.nested.list", [1, 2, 3])
        config.set("complex.other", "value")
        
        # Create a partial override
        override = {
            "complex": {
                "nested": {
                    "value": 99,
                    "additional": "extra"
                }
            }
        }
        
        # Use internal method to merge
        config._deep_merge(config._config, override)
        
        # Check that merge was done correctly
        self.assertEqual(config.get("complex.nested.value"), 99)  # Overridden
        self.assertEqual(config.get("complex.nested.additional"), "extra")  # Added
        self.assertEqual(config.get("complex.nested.list"), [1, 2, 3])  # Preserved
        self.assertEqual(config.get("complex.other"), "value")  # Preserved
    
    def test_value_conversion(self):
        """Test value type conversion."""
        config = ConfigManager()
        
        # Test various conversions
        self.assertEqual(config._convert_value("true"), True)
        self.assertEqual(config._convert_value("FALSE"), False)
        self.assertEqual(config._convert_value("yes"), True)
        self.assertEqual(config._convert_value("no"), False)
        self.assertEqual(config._convert_value("42"), 42)
        self.assertEqual(config._convert_value("3.14"), 3.14)
        self.assertEqual(config._convert_value("hello"), "hello")
        
        # Test list conversion
        self.assertEqual(config._convert_value("[1, 2, 3]"), [1, 2, 3])
        
        # Test dict conversion
        self.assertEqual(config._convert_value('{"a": 1, "b": 2}'), {"a": 1, "b": 2})

if __name__ == "__main__":
    unittest.main()
