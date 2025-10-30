# Example Workflow Plugin

A simple example workflow plugin demonstrating the GAO-Dev plugin API for custom workflows.

## Overview

This plugin provides a basic workflow that demonstrates:
- Implementing `BaseWorkflowPlugin`
- Creating a custom workflow class
- Declaring required permissions
- Basic workflow functionality

## Structure

```
example_workflow_plugin/
  __init__.py                 # Package marker
  plugin.yaml                 # Plugin metadata
  workflow_plugin.py          # BaseWorkflowPlugin implementation
  workflow.py                 # IWorkflow implementation
  README.md                   # This file
```

## Usage

### 1. Create Your Workflow Class

Implement `IWorkflow` interface:

```python
from gao_dev.core.interfaces.workflow import IWorkflow
from gao_dev.core.models.workflow import WorkflowIdentifier, WorkflowResult

class MyWorkflow(IWorkflow):
    @property
    def identifier(self) -> WorkflowIdentifier:
        return WorkflowIdentifier("my-workflow", phase=1)

    @property
    def description(self) -> str:
        return "My custom workflow"

    @property
    def required_tools(self) -> List[str]:
        return ["Read", "Write"]

    async def execute(self, context):
        # Your implementation
        return WorkflowResult(
            success=True,
            artifacts=[],
            message="Workflow complete"
        )

    def validate_context(self, context) -> bool:
        return True
```

### 2. Create Your Plugin Class

Extend `BaseWorkflowPlugin`:

```python
from gao_dev.plugins import BaseWorkflowPlugin, WorkflowMetadata
from gao_dev.core.models.workflow import WorkflowIdentifier

class MyWorkflowPlugin(BaseWorkflowPlugin):
    def get_workflow_class(self):
        return MyWorkflow

    def get_workflow_identifier(self):
        return WorkflowIdentifier("my-workflow", phase=1)

    def get_workflow_metadata(self):
        return WorkflowMetadata(
            name="my-workflow",
            description="My custom workflow",
            phase=1,
            tags=["custom"],
            required_tools=["Read", "Write"]
        )
```

### 3. Create plugin.yaml

```yaml
name: my-workflow-plugin
version: 1.0.0
type: workflow
entry_point: my_workflow_plugin.workflow_plugin.MyWorkflowPlugin
description: "My custom workflow"
author: "Your Name"
enabled: true
permissions:
  - file:read
  - file:write
  - hook:register
timeout_seconds: 60
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

### 5. Use Your Workflow

```python
from gao_dev.plugins import WorkflowPluginManager
from gao_dev.core.workflow_registry import WorkflowRegistry

# Set up plugin manager
manager = WorkflowPluginManager(discovery, loader, registry)

# Discover and load plugins
manager.load_workflow_plugins()
manager.register_workflow_plugins()

# Get and execute your workflow
workflow = registry.get_workflow("my-workflow")
result = await workflow.execute(context)
```

## Key Points

- Workflow plugins must implement `IWorkflow` interface
- Plugin class must extend `BaseWorkflowPlugin`
- Workflow identifiers must be unique
- Workflows are organized by BMAD phase (1-4, or -1 for phase-independent)
- Lifecycle hooks (`initialize()`, `cleanup()`) are optional
- Declare all required permissions in plugin.yaml

## Permissions

This example plugin requires:
- `file:read` - Read files during workflow execution
- `file:write` - Write workflow outputs
- `hook:register` - Register workflow lifecycle hooks

## Testing

```bash
pytest tests/plugins/test_workflow_plugin.py -v
```

## License

MIT License - See GAO-Dev project for details
