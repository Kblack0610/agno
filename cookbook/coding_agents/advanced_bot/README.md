# Advanced Validation Bot

A validation bot that leverages the Model Capability Provider (MCP) for prompt-based validation orchestration.

## Overview

This project implements an advanced validation bot that uses natural language prompts to dynamically determine and execute validation tasks. It integrates with the MCP for sequential thinking, allowing it to break down complex validation tasks into logical steps and provide comprehensive feedback.

## Features

- **Prompt-Based Validation**: Run validation tasks using natural language prompts
- **MCP Integration**: Leverage sequential thinking for intelligent validation orchestration
- **Configurable Validation Profiles**: Customize validation thresholds and requirements
- **Multiple Validation Types**: Support for test, lint, security, and more
- **Detailed Reporting**: Get comprehensive reports on validation results
- **Mock MCP Implementation**: Test validation flows without requiring the actual MCP server

## Project Structure

```
advanced_bot/
├── agents/               # Validation agents for different validation types
│   ├── test_validation_agent.py
│   └── ...
├── config/               # Configuration management
│   ├── config_manager.py
│   ├── validation_profile.py
│   └── examples/         # Example configuration profiles
│       ├── strict.yaml
│       ├── standard.yaml
│       └── ...
├── core/                 # Core functionality
│   ├── sequential_orchestrator.py
│   └── ...
├── docs/                 # Documentation
│   ├── prompt_validation_guide.md
│   └── ...
├── examples/             # Example scripts
│   ├── prompt_validation_examples.py
│   └── ...
├── mock_mcp.py           # Mock MCP implementation
├── setup_mcp.py          # MCP setup script
└── validate_with_prompt.py # Main validation script
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for MCP integration)

### Installation

1. Clone the repository
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Set up the MCP environment:
```
python setup_mcp.py
```

### Usage

Run validation with a prompt:
```
python validate_with_prompt.py "Please validate my test coverage"
```

Use different validation profiles:
```
python validate_with_prompt.py "Check code quality" --profile strict
```

Specify validation types:
```
python validate_with_prompt.py "Check for security issues" --validation-types security,lint
```

Run validation on a specific directory:
```
python validate_with_prompt.py "Validate this module" --target ./src/module
```

### Examples

Run example validation scenarios:
```
python examples/prompt_validation_examples.py
```

## Documentation

For detailed usage instructions, see [Prompt Validation Guide](docs/prompt_validation_guide.md).

## Development

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

## Future Enhancements

1. Implement the actual MCP integration when the agno package is available
2. Add more validation types (complexity, security, etc.)
3. Create a web interface for the validation bot
4. Implement more sophisticated prompt understanding capabilities

## License

This project is licensed under the MIT License.
