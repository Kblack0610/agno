# Configuration System Usage Guide

The continuous validation bot includes a robust configuration system that supports:
- YAML and JSON configuration files
- Environment variable overrides
- Validation profiles (strict, standard, minimal, and custom)
- Nested configuration settings with dot notation access

This guide demonstrates how to use the configuration system effectively.

## Configuration Files

Configuration can be loaded from YAML or JSON files. The system supports:

1. **Single Configuration File**: Load from a single file
2. **Directory of Configuration Files**: Load from multiple files in a directory, merged in alphabetical order
3. **Environment Variable Overrides**: Override any configuration using environment variables

### Example Configuration Files

The `config/examples/` directory contains pre-defined configuration profiles:

- `standard.yaml`: Balanced thresholds for most projects (default)
- `strict.yaml`: High thresholds for critical projects
- `minimal.yaml`: Lower thresholds for rapid development
- `custom.yaml`: Example of customized validation settings

## Validation Profiles

Validation profiles define the thresholds and requirements for different validation types:

| Profile  | Test Coverage | Complexity | Lint Errors | Lint Warnings | Type Check | Security Scan | Performance |
|----------|---------------|------------|-------------|---------------|------------|---------------|-------------|
| strict   | 90%           | 7          | 0           | 5             | Required   | Required      | Required    |
| standard | 70%           | 10         | 0           | 10            | Required   | Not Required  | Not Required|
| minimal  | 50%           | 15         | 5           | 20            | Not Required| Not Required | Not Required|
| custom   | User-defined  | User-defined| User-defined| User-defined  | User-defined| User-defined | User-defined|

## End-to-End Usage

### Command Line Interface

The validation bot can be run directly from the command line:

```bash
python main.py --target /path/to/project --validation-type test --config config/examples/standard.yaml
```

#### Command Line Options

- `--config`, `-c`: Path to configuration file or directory
- `--profile`, `-p`: Validation profile to use (overrides configuration file)
- `--target`, `-t`: Target directory or file to validate (required)
- `--validation-type`: Type of validation to perform (test, lint, type_check, security, performance)
- `--verbose`, `-v`: Enable verbose output

### Using Environment Variables

Environment variables can override any configuration setting using the `VALBOT_` prefix:

```bash
# Set validation profile
export VALBOT_VALIDATION_PROFILE=strict

# Override test coverage threshold
export VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD=85

# Disable test validation
export VALBOT_AGENTS_TEST_VALIDATION_ENABLED=false

# Run the validation with env var overrides
python main.py --target /path/to/project --validation-type test
```

## Programmatic Usage

### Basic Usage

```python
from config.config_manager import ConfigManager
from config.validation_profile import ValidationProfile

# Load configuration from file
config = ConfigManager("config/examples/standard.yaml")

# Get a configuration value
profile_name = config.get("validation.profile")  # Using dot notation
timeout = config.get("validation.timeout", 30)   # With default value

# Set a configuration value
config.set("validation.timeout", 60)

# Access the validation profile
profile = ValidationProfile(profile_name, config)

# Check if validation is required
if profile.is_validation_required("test"):
    print("Test validation is required")
    
# Check if a threshold is met
coverage = 75
if profile.is_threshold_met("test_coverage", coverage):
    print(f"Test coverage of {coverage}% meets the threshold")
```

### Advanced Usage with Orchestrator

```python
from core.sequential_orchestrator import SequentialOrchestrator
from agents.test_validation_agent import TestValidationAgent

# Initialize the orchestrator with configuration
orchestrator = SequentialOrchestrator(config_path="config/examples/strict.yaml")

# Start a validation chain
result = orchestrator.start_validation_chain(
    prompt="Validate the test coverage of this project",
    validation_type="test",
    initial_context={"project_path": "/path/to/project"}
)

# Initialize a validation agent with configuration
agent = TestValidationAgent(config_path="config/examples/strict.yaml")

# Run test validation
validation_result = agent.validate_tests(
    directory="/path/to/project/tests",
    test_type="pytest",
    coverage=True
)
```

## Example Scenarios

### 1. Basic Test Validation

```bash
# Use the standard profile
python main.py --target ./tests --validation-type test
```

### 2. Strict Validation for Critical Code

```bash
# Use the strict profile for a critical component
python main.py --target ./critical_module --validation-type test --profile strict
```

### 3. Minimal Validation for Rapid Development

```bash
# Use minimal validation during early development
python main.py --target ./prototype --validation-type test --profile minimal
```

### 4. Custom Validation with Environment Variables

```bash
# Set custom thresholds with environment variables
export VALBOT_VALIDATION_PROFILE=custom
export VALBOT_VALIDATION_CUSTOM_PROFILE_TEST_COVERAGE_THRESHOLD=80
export VALBOT_VALIDATION_CUSTOM_PROFILE_FAIL_ON_ANY_ISSUE=true

# Run validation with custom settings
python main.py --target ./project --validation-type test
```

## Troubleshooting

### Debugging Configuration Loading

Use the `--verbose` flag to see detailed information about configuration loading:

```bash
python main.py --target ./tests --validation-type test --verbose
```

### Environment Variable Precedence

Remember that environment variables take precedence over configuration files. To view the current active configuration:

```python
from config.config_manager import ConfigManager

config = ConfigManager()
print(config.to_string())  # Prints the entire configuration
```

## Extending the Configuration System

To add new configuration sections:

1. Add default values in `ConfigManager._load_defaults()`
2. Access the values using the dot notation pattern
3. Use environment variables with the `VALBOT_` prefix to override values
