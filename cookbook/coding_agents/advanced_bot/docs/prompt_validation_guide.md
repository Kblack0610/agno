# Prompt-Based Validation Guide

This guide explains how to use the prompt-based validation system with MCP (Model Capability Provider) integration for automated code validation.

## Overview

The prompt-based validation system allows you to run validation tasks based on natural language prompts. It leverages the power of MCP for sequential thinking and orchestration, enabling intelligent analysis of validation requirements and execution of appropriate validation tools.

### Key Features

- **Natural Language Prompts**: Describe your validation needs in plain English
- **Sequential Thinking**: Uses MCP to break down validation tasks into logical steps
- **Profile-Based Configuration**: Customize validation thresholds using profiles
- **Multiple Validation Types**: Support for test, lint, security, and other validation types
- **Detailed Reporting**: Get comprehensive reports on validation results

## Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for MCP integration)

### Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the MCP environment:
   ```bash
   python setup_mcp.py
   ```

## Usage

### Basic Usage

To run a validation with a prompt:

```bash
python validate_with_prompt.py "Please validate my test coverage"
```

### Advanced Options

#### Specifying a Validation Profile

Use the `--profile` option to specify a validation profile:

```bash
python validate_with_prompt.py "Check my code quality" --profile strict
```

Available profiles:
- `strict`: Enforces high standards for all validation types
- `standard`: Balanced validation thresholds (default)
- `minimal`: Minimal validation requirements
- `custom`: Uses custom validation thresholds from a configuration file

#### Specifying Validation Types

Use the `--validation-types` option to specify which validation types to run:

```bash
python validate_with_prompt.py "Check for security issues" --validation-types security,lint
```

Available validation types:
- `test`: Test coverage and quality
- `lint`: Code style and quality
- `security`: Security vulnerabilities
- `type`: Type checking
- `complexity`: Code complexity (experimental)

#### Specifying a Target Directory

Use the `--target` option to specify the directory to validate:

```bash
python validate_with_prompt.py "Validate this module" --target ./src/module
```

#### Enabling Verbose Output

Use the `--verbose` option to enable detailed logging:

```bash
python validate_with_prompt.py "Run comprehensive validation" --verbose
```

### Example Commands

```bash
# Validate test coverage with standard profile
python validate_with_prompt.py "Please validate my test coverage"

# Check code quality with strict profile
python validate_with_prompt.py "Check my code quality" --profile strict

# Run security validation only
python validate_with_prompt.py "Check for security issues" --validation-types security

# Run comprehensive validation with all types
python validate_with_prompt.py "Run comprehensive validation" --validation-types test,lint,security,type,complexity

# Validate a specific directory
python validate_with_prompt.py "Validate this module" --target ./src/module
```

## Configuration

### Validation Profiles

Validation profiles define the thresholds and requirements for each validation type. They are stored in YAML files in the `config/examples` directory.

#### Example Profile Configuration

```yaml
# config/examples/standard.yaml
validation:
  profile: standard
  test:
    required: true
    coverage_threshold: 70
    test_quality_threshold: 80
  lint:
    required: true
    error_threshold: 0
    warning_threshold: 10
  security:
    required: false
    vulnerability_threshold: 0
  type:
    required: false
    error_threshold: 0
```

### Environment Variables

You can override configuration settings using environment variables with the `VALBOT_` prefix:

```bash
VALBOT_VALIDATION_TEST_COVERAGE_THRESHOLD=80 python validate_with_prompt.py "Check test coverage"
```

## MCP Integration

The validation bot integrates with MCP for sequential thinking, allowing it to:

1. Parse and understand user prompts
2. Determine required validation types
3. Break down validation tasks into logical steps
4. Execute validation tools
5. Analyze results against profile requirements
6. Generate meaningful responses

### Mock MCP Implementation

For development and testing purposes, a mock MCP implementation is provided in `mock_mcp.py`. This allows you to test the validation system without requiring the actual MCP server.

## Extending the System

### Adding New Validation Types

To add a new validation type:

1. Create a new validation agent in the `agents` directory
2. Update the `ValidationProfile` class to include the new type
3. Add the new type to the orchestrator's validation flow

### Creating Custom Profiles

To create a custom validation profile:

1. Create a new YAML file in the `config/examples` directory
2. Define the validation thresholds and requirements
3. Use the profile with the `--profile` option

## Troubleshooting

### Common Issues

- **API Key Not Found**: Make sure your OpenAI API key is set in the environment
- **Configuration File Not Found**: Check the path to your configuration file
- **Validation Type Not Supported**: Make sure the validation type is supported and implemented

### Logging

Enable verbose logging with the `--verbose` option to get more details on execution:

```bash
python validate_with_prompt.py "Check my code" --verbose
```

## Contributing

Contributions to improve the validation bot are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
