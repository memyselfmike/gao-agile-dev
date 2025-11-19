# GAO-Dev Quick Start Guide

Get up and running with GAO-Dev in under 5 minutes.

## Prerequisites

- Python 3.10 or higher
- Git installed
- One of the following AI providers:
  - Claude Code CLI (recommended)
  - OpenCode CLI
  - Direct API key (Anthropic or OpenAI)
  - Local Ollama installation

## Installation

### Step 1: Install GAO-Dev

```bash
# Clone the repository
git clone https://github.com/your-org/gao-agile-dev.git
cd gao-agile-dev

# Install in development mode
pip install -e .

# Verify installation
gao-dev --version
```

### Step 2: Start GAO-Dev

```bash
gao-dev start
```

That's it! On first run, GAO-Dev will:
1. Detect your environment
2. Guide you through provider selection
3. Initialize your project workspace

## First Interaction

When you start GAO-Dev, Brian (your workflow coordinator) will greet you:

```
+--------------------------------------------------+
|  Welcome to GAO-Dev!                             |
|  I'm Brian, your development workflow            |
|  coordinator.                                    |
+--------------------------------------------------+

What would you like to build today?
>
```

### Try These Commands

**Natural language works:**
```
> Build a todo app with user authentication
> Create a REST API for inventory management
> Help me understand this codebase
```

**Or use direct commands:**
```
> /help              # Show available commands
> /status            # Show project status
> /list-workflows    # List available workflows
> exit               # Exit the REPL
```

## Provider Selection

On first run, you'll select an AI provider:

```
Select AI Provider
+-----------------+----------------------------------+
| Provider        | Description                      |
+-----------------+----------------------------------+
| claude-code     | Anthropic's Claude Code CLI      |
| opencode        | OpenCode CLI with local models   |
| direct-api      | Direct API calls                 |
+-----------------+----------------------------------+

Enter selection: claude-code
```

Your preference is saved to `.gao-dev/provider_preferences.yaml`.

## Starting a New Project

### Option 1: Greenfield (New Project)

```
> Build a task management app with React

Brian: I'll help you build that! Let me analyze the requirements...

Scale Level: 2 (Small Feature)
Estimated Stories: 5-8
Duration: 1-2 weeks

Would you like me to:
1. Create the PRD first
2. Generate the architecture
3. Start with stories directly

> 1
```

### Option 2: Brownfield (Existing Project)

Navigate to your existing project and start GAO-Dev:

```bash
cd /path/to/your/project
gao-dev start
```

Brian will detect the existing codebase and offer to:
- Analyze the codebase structure
- Generate documentation
- Create improvement stories

## Common Operations

### Create Documentation

```bash
# Create a PRD for a new feature
gao-dev create-prd --name "User Authentication"

# Create architecture documentation
gao-dev create-architecture --name "User Authentication"
```

### Implement Features

```bash
# Implement a specific story
gao-dev implement-story --epic 1 --story 1

# Run the full workflow
gao-dev run-workflow planning
```

### Check Status

```bash
# System health check
gao-dev health

# List available agents
gao-dev list-agents

# List workflows
gao-dev list-workflows
```

## Environment Variables

For CI/CD or automated environments, you can skip interactive prompts:

```bash
# Set provider via environment variable
export AGENT_PROVIDER=claude-code

# Set API key for direct API usage
export ANTHROPIC_API_KEY=sk-ant-...

# Start without prompts
gao-dev start
```

## Project Structure

GAO-Dev creates a `.gao-dev/` directory in your project:

```
your-project/
+-- .gao-dev/
|   +-- documents.db           # Document lifecycle tracking
|   +-- context.json           # Execution context
|   +-- provider_preferences.yaml  # Your provider settings
|   +-- metrics/               # Performance metrics
+-- docs/                      # Generated documentation
+-- src/                       # Your application code
+-- tests/                     # Test suite
```

## Next Steps

- **Docker Deployment**: See [Docker Deployment Guide](./docker-deployment.md)
- **Environment Variables**: See [Environment Variables Reference](../guides/environment-variables.md)
- **Troubleshooting**: See [Common Errors](../troubleshooting/common-errors.md)
- **Full Documentation**: See [Documentation Index](../INDEX.md)

## Getting Help

```bash
# Show all commands
gao-dev --help

# Show help for specific command
gao-dev start --help

# Check system health
gao-dev health
```

For issues or questions:
- Check the [Troubleshooting Guide](../troubleshooting/common-errors.md)
- Review logs in `.gao-dev/metrics/`
- See [FAQ](../features/interactive-provider-selection/FAQ.md)

---

**Time to complete**: Under 5 minutes
**Last Updated**: 2025-11-19
