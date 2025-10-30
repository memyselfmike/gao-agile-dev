# GAO-Dev Plugin Template

A complete template for creating custom GAO-Dev plugins. Copy this template to start building your own plugin.

## Quick Start

### 1. Copy the Template

```bash
# Copy template to your plugin directory
cp -r examples/plugin-template my-custom-plugin
cd my-custom-plugin
```

### 2. Replace Placeholders

Replace these placeholders throughout all files:

- `MY_PLUGIN_NAME` → Your plugin name in kebab-case (e.g., `my-custom-plugin`)
- `MY_PLUGIN` → Your plugin name for documentation (e.g., `My Custom Plugin`)
- `MY_ENTRY_POINT` → Python path to your plugin class (e.g., `my_plugin.agent_plugin.MyAgentPlugin`)
- `MyAgent` → Your agent class name (e.g., `MyCustomAgent`)
- `MyAgentPlugin` → Your plugin class name (e.g., `MyCustomAgentPlugin`)
- `YOUR_NAME` → Your name or organization

**Files to update**:
- `__init__.py` - Package docstring
- `plugin.yaml` - All metadata fields
- `agent_plugin.py` - Class names and docstrings
- `agent.py` - Class names, docstrings, defaults
- This `README.md` - Project-specific documentation

### 3. Customize Your Agent

Edit `agent.py` to implement your agent's behavior:

```python
class MyAgent(IAgent):
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        # Your agent logic here
        # Call Claude API, process files, generate artifacts, etc.
        pass
```

### 4. Configure Metadata

Edit `agent_plugin.py` to set agent metadata:

```python
def get_agent_metadata(self):
    return AgentMetadata(
        name="MyAgent",
        role="My Role",  # What does this agent do?
        description="Brief description",
        capabilities=["cap1", "cap2"],  # What can it do?
        tools=["Read", "Write", "Grep"],  # What tools does it need?
        model="claude-sonnet-4-5-20250929"
    )
```

### 5. Declare Permissions

Edit `plugin.yaml` to declare required permissions:

```yaml
permissions:
  - file:read        # Read files
  - file:write       # Write files
  # - file:delete    # Delete files
  # - network:request # Make network requests
  # - subprocess:execute # Run commands
  # - hook:register  # Register lifecycle hooks
  # - config:read    # Read configuration
  # - config:write   # Write configuration
  # - database:read  # Read from database
  # - database:write # Write to database
```

**Only request permissions you actually need!**

### 6. Add Hooks (Optional)

Edit `agent_plugin.py` to register lifecycle hooks:

```python
def register_hooks(self):
    if self._hook_manager:
        from gao_dev.core import HookEventType

        self._hook_manager.register_hook(
            HookEventType.WORKFLOW_START,
            self._on_workflow_start,
            priority=100,
            plugin_name="my-plugin"
        )

def _on_workflow_start(self, event_data):
    # Handle workflow start
    pass
```

### 7. Install Dependencies

Edit `requirements.txt` to add any dependencies:

```txt
# Add your dependencies here
# requests>=2.31.0
# pydantic>=2.0.0
```

### 8. Write Tests

Create tests in `tests/test_agent.py`:

```python
def test_my_agent_basic():
    agent = MyAgent()
    result = await agent.execute("test task")
    assert result is not None
```

### 9. Install Your Plugin

```bash
# Development install
pip install -e .

# Or copy to GAO-Dev plugins directory
cp -r . ~/.gao-dev/plugins/my-custom-plugin
```

### 10. Test Your Plugin

```bash
# Run tests
pytest tests/ -v

# Test with GAO-Dev
gao-dev list-agents  # Should show your agent
```

## Template Structure

```
plugin-template/
  __init__.py                 # Package marker with version
  plugin.yaml                 # Plugin metadata and configuration
  agent_plugin.py             # BaseAgentPlugin implementation
  agent.py                    # IAgent implementation (your logic here)
  requirements.txt            # Dependencies
  tests/
    test_agent.py             # Test suite
  README.md                   # This file
```

## Available Permissions

Declare only the permissions your plugin needs:

| Permission | Description |
|------------|-------------|
| `file:read` | Read files from filesystem |
| `file:write` | Write files to filesystem |
| `file:delete` | Delete files |
| `network:request` | Make HTTP/HTTPS requests |
| `subprocess:execute` | Execute shell commands |
| `hook:register` | Register lifecycle hooks |
| `config:read` | Read GAO-Dev configuration |
| `config:write` | Modify GAO-Dev configuration |
| `database:read` | Read from database |
| `database:write` | Write to database |

## Lifecycle Methods

Override these optional methods in your plugin:

```python
class MyAgentPlugin(BaseAgentPlugin):
    def initialize(self):
        """Called after plugin is loaded."""
        # Setup connections, load resources
        return True

    def cleanup(self):
        """Called before plugin is unloaded."""
        # Close connections, release resources
        pass

    def register_hooks(self):
        """Register lifecycle hooks."""
        # Register event handlers
        pass
```

## Hook Events

Available lifecycle events to hook into:

- `HookEventType.WORKFLOW_START` - Workflow begins
- `HookEventType.WORKFLOW_END` - Workflow completes
- `HookEventType.WORKFLOW_ERROR` - Workflow fails
- `HookEventType.AGENT_CREATED` - Agent created
- `HookEventType.AGENT_EXECUTE_START` - Agent starts task
- `HookEventType.AGENT_EXECUTE_END` - Agent completes task
- `HookEventType.PLUGIN_LOADED` - Plugin loaded
- `HookEventType.PLUGIN_UNLOADED` - Plugin unloaded
- `HookEventType.PLUGIN_ERROR` - Plugin error
- `HookEventType.SYSTEM_STARTUP` - GAO-Dev starts
- `HookEventType.SYSTEM_SHUTDOWN` - GAO-Dev stops

## Configuration Options

**plugin.yaml** fields:

```yaml
name: my-plugin           # Required: Unique kebab-case name
version: 1.0.0            # Required: Semantic version
type: agent               # Required: agent, workflow, methodology, tool
entry_point: my.Plugin    # Required: Python path to plugin class
description: "..."        # Required: Brief description
author: "Your Name"       # Required: Author name
enabled: true             # Optional: Enable/disable (default: true)
permissions: []           # Optional: Required permissions
timeout_seconds: 30       # Optional: Initialization timeout (default: 30)
```

## Testing Checklist

- [ ] All placeholders replaced
- [ ] Agent logic implemented
- [ ] Metadata configured
- [ ] Permissions declared (minimal set)
- [ ] Tests written and passing
- [ ] Dependencies listed
- [ ] Documentation updated
- [ ] Plugin installs successfully
- [ ] Plugin shows in `gao-dev list-agents`
- [ ] Agent executes tasks correctly

## Best Practices

1. **Minimal Permissions**: Only request permissions you actually use
2. **Error Handling**: Use try/except and log errors properly
3. **Async Support**: Use `async def execute()` for I/O operations
4. **Type Hints**: Add type hints to all public methods
5. **Documentation**: Document all public methods with docstrings
6. **Testing**: Achieve 80%+ test coverage
7. **Logging**: Use structlog for consistent logging
8. **Validation**: Validate inputs in `validate_task()`

## Example Plugins

See these examples for reference:

- `tests/plugins/fixtures/example_agent_plugin/` - Basic agent plugin
- `tests/plugins/fixtures/example_workflow_plugin/` - Workflow plugin

## Documentation

For complete documentation, see:

- **Plugin Development Guide**: `docs/plugin-development-guide.md`
- **Plugin API Reference**: Plugin Development Guide section 13
- **Example Plugins**: `tests/plugins/fixtures/`

## Need Help?

- Check the Plugin Development Guide for detailed tutorials
- Look at example plugins for reference implementations
- Review the GAO-Dev documentation for core concepts

## License

Same as GAO-Dev project (check main repository for license details).
