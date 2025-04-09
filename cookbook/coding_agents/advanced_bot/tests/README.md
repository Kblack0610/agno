# Tests for Advanced Validation Bot

This directory contains tests for the advanced validation bot with validation steps between each test.

## Overview

The tests are designed to validate the functionality of each component of the advanced validation bot:

1. **Coder Bot** - Tests code generation, modification, and analysis
2. **Validation Primitives** - Tests the validation result structure and registry
3. **Sequential Orchestrator** - Tests the sequential thinking orchestration
4. **End-to-End Workflow** - Tests the complete workflow from code creation to fixing

## Running the Tests

To run all tests with validation steps:

```bash
python run_tests.py
```

This will run each test in sequence with validation steps between them.

## Test Structure

Each test follows this structure:

1. Run the test for a specific component
2. Capture the test results
3. Run a validation step to verify the results
4. Report the validation results
5. Continue to the next test

The validation steps simulate what would normally be done using the Sequential Thinking MCP for more advanced reasoning.

## Validation Steps

Validation steps verify the results of each test and provide insights into the functioning of each component. In a real implementation, these would use the Sequential Thinking MCP to perform detailed analysis of test results.

## Test Files

- `test_runner.py` - Contains the test classes and methods
- `run_tests.py` - Script to run all tests in sequence
