# Example Agent Plugin

This is an example agent plugin for GAO-Dev that demonstrates how to create custom agent plugins.

## Structure

```
example_agent_plugin/
├── __init__.py           # Package marker
├── plugin.yaml          # Plugin metadata
├── agent.py            # Agent implementation (IAgent)
├── agent_plugin.py     # Plugin implementation (BaseAgentPlugin)
└── README.md           # This file
```

## Usage

### 1. Create Your Agent Class

Implement `IAgent` interface or extend `BaseAgent`:

```python
from gao_dev.agents.base import BaseAgent

class MyAgent(BaseAgent):
    async def execute_task(self, task, context):
        yield "Starting..."
        # Your implementation
        yield "Complete!"
```

### 2. Create Your Plugin Class

Extend `BaseAgentPlugin`:

```python
from gao_dev.plugins import BaseAgentPlugin, AgentMetadata

class MyAgentPlugin(BaseAgentPlugin):
    def get_agent_class(self):
        return MyAgent

    def get_agent_name(self):
        return "MyAgent"

    def get_agent_metadata(self):
        return AgentMetadata(
            name="MyAgent",
            role="My Role",
            description="My custom agent",
            capabilities=["custom"],
            tools=["Read", "Write"]
        )
```

### 3. Create plugin.yaml

```yaml
name: my-agent-plugin
version: 1.0.0
type: agent
entry_point: my_agent_plugin.agent_plugin.MyAgentPlugin
description: "My custom agent"
author: "Your Name"
enabled: true
permissions:
  - file:read
  - file:write
  - hook:register
timeout_seconds: 30
```

#### Available Permissions:
- `file:read` - Read files
- `file:write` - Write files
- `file:delete` - Delete files
- `network:request` - Make network requests
- `subprocess:execute` - Execute subprocesses
- `hook:register` - Register lifecycle hooks
- `config:read` - Read configuration
- `config:write` - Write configuration
- `database:read` - Read from database
- `database:write` - Write to database

### 4. Install Plugin

Place your plugin in one of the configured plugin directories:
- `./plugins`
- `~/.gao-dev/plugins`

### 5. Use Your Agent

```python
from gao_dev.plugins import AgentPluginManager
from gao_dev.core.factories.agent_factory import AgentFactory

# Set up plugin manager
manager = AgentPluginManager(discovery, loader, factory)

# Discover and load plugins
manager.load_agent_plugins()
manager.register_agent_plugins()

# Use your agent
agent = factory.create_agent("myagent")
async for msg in agent.execute_task("Do something", context):
    print(msg)
```

## Key Points

- Agent plugins must implement `IAgent` interface
- Plugin class must extend `BaseAgentPlugin`
- Agent names must be unique across all agents
- Plugins are discovered automatically from configured directories
- Lifecycle hooks (`initialize()`, `cleanup()`) are optional
