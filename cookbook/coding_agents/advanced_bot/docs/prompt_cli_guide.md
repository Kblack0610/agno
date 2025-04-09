# Run the full workflow
cd /home/kblack0610/dev/AI/agno/cookbook/coding_agents/advanced_bot
python cli.py run "Create a simple Python calculator application" --workspace-dir ./output --mock-mcp --continuous-validation

# Just create a plan
python cli.py plan "Create a simple Flask web API" --target-dir ./output --mock-mcp --output plan.json

# Execute an existing plan
python cli.py execute plan.json --workspace-dir ./output --continuous-validation

# Validate existing code
python cli.py validate ./output --validation-types test,lint
