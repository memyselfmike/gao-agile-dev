# GAO-Dev Plugin Development Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-30
**Audience**: Plugin Developers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Plugin Types](#plugin-types)
4. [Core Concepts](#core-concepts)
5. [Agent Plugins](#agent-plugins)
6. [Workflow Plugins](#workflow-plugins)
7. [Hooks System](#hooks-system)
8. [Permissions](#permissions)
9. [Configuration](#configuration)
10. [Testing](#testing)
11. [Working with Project-Scoped Document Lifecycle](#working-with-project-scoped-document-lifecycle)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)
14. [API Reference](#api-reference)

---

## Introduction

### What are GAO-Dev Plugins?

GAO-Dev plugins are Python packages that extend GAO-Dev functionality without modifying core code. Plugins can add:
- **Custom Agents**: Specialized AI agents for specific tasks
- **Custom Workflows**: Domain-specific development workflows
- **Event Listeners**: React to lifecycle events via hooks

### Use Cases

- **Domain-Specific Agents**: Financial analysis, legal document review, scientific research
- **Industry Workflows**: Healthcare compliance, financial reporting, legal discovery
- **Integration Tools**: Connect with proprietary systems, custom APIs, legacy software
- **Monitoring & Metrics**: Track usage, performance, quality metrics

### Plugin Architecture Overview

```
GAO-Dev Core
    |
    ├── Plugin Discovery (finds plugins)
    ├── Plugin Loader (loads and validates)
    ├── Plugin Sandbox (enforces security)
    └── Plugin Hooks (lifecycle events)
         |
         └── Your Plugin
              ├── Agent/Workflow Implementation
              ├── Permissions Declaration
              └── Hook Registrations
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- GAO-Dev installed
- Basic understanding of async/await

### Create Your First Plugin (5 minutes)

**1. Create Plugin Directory**

```bash
mkdir -p plugins/hello_plugin
cd plugins/hello_plugin
```

**2. Create Package Structure**

```bash
touch __init__.py
touch plugin.yaml
touch agent.py
touch agent_plugin.py
```

**3. Write plugin.yaml**

```yaml
name: hello-plugin
version: 1.0.0
type: agent
entry_point: hello_plugin.agent_plugin.HelloAgentPlugin
description: "My first GAO-Dev plugin"
author: "Your Name"
enabled: true
permissions:
  - file:read
timeout_seconds: 30
```

**4. Create Agent (agent.py)**

```python
from gao_dev.agents.base import BaseAgent

class HelloAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="HelloAgent",
            role="Greeter",
            persona="A friendly agent that greets users",
            tools=["Read"],
            model="claude-sonnet-4-5-20250929"
        )

    async def execute_task(self, task, context):
        yield "Hello! I'm your custom agent."
        yield f"Task: {task}"
        yield "Task complete!"
```

**5. Create Plugin (agent_plugin.py)**

```python
from gao_dev.plugins import BaseAgentPlugin, AgentMetadata
from .agent import HelloAgent

class HelloAgentPlugin(BaseAgentPlugin):
    def get_agent_class(self):
        return HelloAgent

    def get_agent_name(self):
        return "HelloAgent"

    def get_agent_metadata(self):
        return AgentMetadata(
            name="HelloAgent",
            role="Greeter",
            description="A friendly greeting agent",
            capabilities=["greeting"],
            tools=["Read"]
        )
```

**6. Test Your Plugin**

```bash
# Discover and load plugins
gao-dev load-plugins

# List available agents (your plugin should appear)
gao-dev list-agents

# Use your agent
gao-dev execute-agent HelloAgent "Say hello"
```

---

## Plugin Types

### Agent Plugins

**Purpose**: Add custom AI agents with specialized capabilities

**Use When**:
- Need domain expertise (legal, medical, financial)
- Require specialized tools or APIs
- Want different persona or behavior

**Base Class**: `BaseAgentPlugin`

### Workflow Plugins

**Purpose**: Add custom development workflows

**Use When**:
- Have domain-specific process
- Need multi-step automated workflows
- Want to extend BMAD methodology

**Base Class**: `BaseWorkflowPlugin`

### Hook-Only Plugins

**Purpose**: Listen to events without providing agents/workflows

**Use When**:
- Collecting metrics or analytics
- Implementing monitoring/alerting
- Integrating with external systems

**Base Class**: `BasePlugin`

---

## Core Concepts

### Plugin Discovery

GAO-Dev automatically discovers plugins from:
- `./plugins` (project-local)
- `~/.gao-dev/plugins` (user-global)
- Configured paths in `config.yaml`

**Discovery Process**:
1. Scan plugin directories
2. Find directories with `__init__.py` and `plugin.yaml`
3. Load and validate `plugin.yaml`
4. Return list of discovered plugins

### Plugin Lifecycle

```
1. Discovery    → Find plugin directories
2. Validation   → Check metadata, permissions, code
3. Loading      → Import and instantiate plugin
4. Initialization → Call initialize() method
5. Registration → Register with factories/registries
6. Active       → Plugin available for use
7. Cleanup      → Call cleanup() before unload
8. Unloaded     → Plugin removed from memory
```

### Plugin Security

**Permission System**: Plugins declare required permissions in `plugin.yaml`. Operations are checked at runtime.

**Sandboxing**: Plugins run with resource limits (memory, CPU) and timeout controls.

**Validation**: Static analysis checks for dangerous code patterns.

---

## Agent Plugins

### Creating an Agent Plugin

**Step 1: Implement IAgent**

Your agent must implement the `IAgent` interface:

```python
from gao_dev.agents.base import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.get("name", "MyAgent"),
            role=kwargs.get("role", "My Role"),
            persona="Agent persona and behavior description",
            tools=["Read", "Write", "Grep"],
            model="claude-sonnet-4-5-20250929"
        )

    async def execute_task(self, task, context):
        """Execute a task and yield progress messages."""
        yield "Starting task..."

        # Your implementation here
        # Access context: context.project_root, context.config
        # Use tools: await self.read_file(path)

        yield "Task complete!"
```

**Step 2: Implement BaseAgentPlugin**

```python
from gao_dev.plugins import BaseAgentPlugin, AgentMetadata

class MyAgentPlugin(BaseAgentPlugin):
    def get_agent_class(self):
        """Return your agent class."""
        return MyAgent

    def get_agent_name(self):
        """Return unique agent name."""
        return "MyAgent"

    def get_agent_metadata(self):
        """Return agent metadata."""
        return AgentMetadata(
            name="MyAgent",
            role="My Role",
            description="What my agent does",
            capabilities=["capability1", "capability2"],
            tools=["Read", "Write", "Grep"],
            model="claude-sonnet-4-5-20250929"
        )
```

**Step 3: Create plugin.yaml**

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
timeout_seconds: 30
```

### Agent Best Practices

- **Single Responsibility**: Each agent should have one clear purpose
- **Clear Persona**: Define agent behavior and personality clearly
- **Tool Selection**: Only request tools you need
- **Error Handling**: Catch and report errors gracefully
- **Progress Updates**: Yield status messages during long operations

---

## Workflow Plugins

### Creating a Workflow Plugin

**Step 1: Implement IWorkflow**

```python
from gao_dev.core.interfaces.workflow import IWorkflow
from gao_dev.core.models.workflow import WorkflowIdentifier, WorkflowResult

class MyWorkflow(IWorkflow):
    @property
    def identifier(self) -> WorkflowIdentifier:
        return WorkflowIdentifier("my-workflow", phase=1)

    @property
    def description(self) -> str:
        return "My custom workflow description"

    @property
    def required_tools(self) -> List[str]:
        return ["Read", "Write", "Grep"]

    async def execute(self, context):
        """Execute workflow steps."""
        # Step 1: Do something
        # Step 2: Do something else
        # Step 3: Complete

        return WorkflowResult(
            success=True,
            artifacts=[],
            message="Workflow complete"
        )

    def validate_context(self, context) -> bool:
        """Validate context before execution."""
        return context.project_root.exists()
```

**Step 2: Implement BaseWorkflowPlugin**

```python
from gao_dev.plugins import BaseWorkflowPlugin, WorkflowMetadata

class MyWorkflowPlugin(BaseWorkflowPlugin):
    def get_workflow_class(self):
        return MyWorkflow

    def get_workflow_identifier(self):
        return WorkflowIdentifier("my-workflow", phase=1)

    def get_workflow_metadata(self):
        return WorkflowMetadata(
            name="my-workflow",
            description="My custom workflow",
            phase=1,  # BMAD phase: 1=Analysis, 2=Planning, 3=Solutioning, 4=Implementation, -1=Any
            tags=["custom", "domain-specific"],
            required_tools=["Read", "Write"]
        )
```

**Step 3: Create plugin.yaml**

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
timeout_seconds: 300
```

### Workflow Best Practices

- **Phase Selection**: Choose appropriate BMAD phase (or -1 for phase-independent)
- **Idempotency**: Workflows should be safely re-runnable
- **Clear Steps**: Break complex workflows into clear steps
- **Context Validation**: Always validate context before execution
- **Error Recovery**: Handle failures gracefully and provide recovery options

---

## Hooks System

### What are Hooks?

Hooks allow plugins to execute code at specific lifecycle events without modifying core code.

### Available Hook Events

```python
from gao_dev.core import HookEventType

# Workflow Events
HookEventType.WORKFLOW_START    # Before workflow execution
HookEventType.WORKFLOW_END      # After successful completion
HookEventType.WORKFLOW_ERROR    # On workflow failure

# Agent Events
HookEventType.AGENT_CREATED     # When agent instantiated
HookEventType.AGENT_EXECUTE_START  # Before agent execution
HookEventType.AGENT_EXECUTE_END    # After agent execution

# Plugin Events
HookEventType.PLUGIN_LOADED     # After plugin loaded
HookEventType.PLUGIN_UNLOADED   # Before plugin unloaded
HookEventType.PLUGIN_ERROR      # On plugin error

# System Events
HookEventType.SYSTEM_STARTUP    # On GAO-Dev startup
HookEventType.SYSTEM_SHUTDOWN   # On GAO-Dev shutdown
```

### Registering Hooks

**In your plugin class**:

```python
from gao_dev.plugins import BasePlugin
from gao_dev.core import HookEventType

class MyPlugin(BasePlugin):
    def register_hooks(self):
        """Register lifecycle hooks."""
        if self._hook_manager:
            self._hook_manager.register_hook(
                HookEventType.WORKFLOW_START,
                self._on_workflow_start,
                priority=100,  # Higher = executes first
                plugin_name="my-plugin"
            )

            self._hook_manager.register_hook(
                HookEventType.WORKFLOW_END,
                self._on_workflow_end,
                priority=100
            )

    def _on_workflow_start(self, event_data):
        """Handle workflow start event."""
        workflow_id = event_data.get("workflow_id")
        print(f"Workflow {workflow_id} starting")

    async def _on_workflow_end(self, event_data):
        """Handle workflow end event (async example)."""
        workflow_id = event_data.get("workflow_id")
        result = event_data.get("result")
        # Log metrics, send notifications, etc.
```

### Hook Execution

- **Priority Order**: Hooks execute in priority order (highest first)
- **Async Support**: Both sync and async hooks supported
- **Error Handling**: Hook errors don't stop workflow execution
- **Return Values**: Hooks can return values (available in results)

### Hook Best Practices

- **Lightweight**: Keep hooks fast (they run synchronously with events)
- **Error Handling**: Catch exceptions to avoid breaking workflows
- **Priority**: Use priority to control execution order
- **Cleanup**: Hooks are automatically unregistered on plugin unload

---

## Permissions

### Permission System Overview

Plugins must declare required permissions in `plugin.yaml`. GAO-Dev enforces permissions at runtime.

### Available Permissions

| Permission | Description | Use Case |
|-----------|-------------|----------|
| `file:read` | Read files | Read source code, config files |
| `file:write` | Write files | Generate code, write reports |
| `file:delete` | Delete files | Cleanup, remove artifacts |
| `network:request` | Make HTTP requests | API calls, web scraping |
| `subprocess:execute` | Execute commands | Run tests, build tools |
| `hook:register` | Register hooks | Monitor lifecycle events |
| `config:read` | Read configuration | Access project settings |
| `config:write` | Write configuration | Modify settings |
| `database:read` | Read from database | Query metrics, history |
| `database:write` | Write to database | Store metrics, logs |

### Declaring Permissions

**In plugin.yaml**:

```yaml
permissions:
  - file:read
  - file:write
  - hook:register
```

### Checking Permissions at Runtime

GAO-Dev automatically enforces permissions. If your plugin attempts an operation without permission, `PermissionDeniedError` is raised.

**Manual Check** (optional):

```python
from gao_dev.plugins import PluginPermission

# Check if plugin has permission
if sandbox.check_permission("my-plugin", PluginPermission.FILE_WRITE):
    # Perform file write
    pass
```

### Permission Best Practices

- **Least Privilege**: Only request permissions you need
- **Document Why**: Comment why each permission is needed
- **Fail Gracefully**: Handle permission denied errors
- **Security Review**: Review permissions before releasing

---

## Configuration

### plugin.yaml Schema

```yaml
# Required Fields
name: my-plugin              # Unique plugin identifier (alphanumeric, hyphens, underscores)
version: 1.0.0               # Semantic version (major.minor.patch)
type: agent                  # Plugin type: agent, workflow, methodology, tool
entry_point: my_plugin.plugin.MyPlugin  # Python path to plugin class

# Optional Fields
description: "Plugin description"  # Human-readable description
author: "Your Name"          # Plugin author
enabled: true                # Whether plugin is enabled (default: true)

# Security Fields
permissions:                 # List of required permissions
  - file:read
  - file:write
  - hook:register
timeout_seconds: 30          # Plugin initialization timeout (default: 30)

# Dependency Fields (future)
dependencies:                # Python package dependencies
  - requests>=2.28.0
  - pydantic>=2.0.0
```

### Example Configurations

**Minimal Configuration**:

```yaml
name: minimal-plugin
version: 1.0.0
type: agent
entry_point: minimal_plugin.plugin.MinimalPlugin
```

**Full Configuration**:

```yaml
name: advanced-plugin
version: 2.1.3
type: workflow
entry_point: advanced_plugin.workflow_plugin.AdvancedWorkflowPlugin
description: "Advanced workflow with custom capabilities"
author: "Advanced Team <team@example.com>"
enabled: true
permissions:
  - file:read
  - file:write
  - network:request
  - database:write
  - hook:register
timeout_seconds: 120
dependencies:
  - requests>=2.28.0
  - pandas>=2.0.0
```

---

## Testing

### Unit Testing Your Plugin

**Test Structure**:

```
my_plugin/
  tests/
    __init__.py
    test_agent.py
    test_plugin.py
```

**Example Test (pytest)**:

```python
import pytest
from my_plugin.agent import MyAgent
from my_plugin.agent_plugin import MyAgentPlugin

def test_agent_creation():
    """Test agent can be created."""
    agent = MyAgent()
    assert agent.name == "MyAgent"
    assert agent.role == "My Role"

@pytest.mark.asyncio
async def test_agent_execute():
    """Test agent execution."""
    agent = MyAgent()
    context = MockContext()

    messages = []
    async for msg in agent.execute_task("test task", context):
        messages.append(msg)

    assert len(messages) > 0
    assert "complete" in messages[-1].lower()

def test_plugin_metadata():
    """Test plugin provides correct metadata."""
    plugin = MyAgentPlugin()
    metadata = plugin.get_agent_metadata()

    assert metadata.name == "MyAgent"
    assert metadata.role == "My Role"
    assert "Read" in metadata.tools
```

### Integration Testing

**Test Plugin Loading**:

```python
def test_plugin_loads():
    """Test plugin can be discovered and loaded."""
    from gao_dev.plugins import PluginDiscovery, PluginLoader

    discovery = PluginDiscovery(config_loader)
    loader = PluginLoader()

    # Discover plugin
    plugins = discovery.discover_plugins([plugin_dir])
    assert len(plugins) > 0

    # Load plugin
    plugin_metadata = plugins[0]
    loader.load_plugin(plugin_metadata)

    # Verify loaded
    assert loader.is_loaded(plugin_metadata.name)
```

### Test Coverage

- **Target**: 80%+ coverage
- **Focus Areas**:
  - Core functionality
  - Error handling
  - Edge cases
  - Integration points

---

## Working with Project-Scoped Document Lifecycle

### Overview

GAO-Dev's document lifecycle system is project-scoped. Each project has its own `.gao-dev/documents.db` for tracking documentation. Plugins that work with documents should respect this project isolation.

### Using Project Lifecycle in Plugins

**Basic Usage**:

```python
from pathlib import Path
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle

class MyPlugin(BasePlugin):
    def on_project_created(self, project_root: Path):
        """Initialize document lifecycle for new project."""
        # Initialize lifecycle for this project
        doc_manager = ProjectDocumentLifecycle.initialize(project_root)

        # Register plugin-specific documents
        doc_manager.registry.register_document(
            path="docs/PLUGIN_CONFIG.md",
            doc_type="plugin-config",
            metadata={"plugin": "my-plugin", "version": "1.0.0"}
        )

    def on_document_created(self, project_root: Path, doc_path: str):
        """Track custom document types."""
        # Get existing manager (project already initialized)
        doc_manager = ProjectDocumentLifecycle.initialize(project_root)

        if doc_path.endswith(".report.md"):
            doc_manager.registry.register_document(
                path=doc_path,
                doc_type="report",
                metadata={"generated_by": "my-plugin"}
            )
```

**Multi-Project Support**:

```python
class MultiProjectPlugin(BasePlugin):
    def process_projects(self, project_roots: List[Path]):
        """Process multiple projects with isolated tracking."""
        for project_root in project_roots:
            # Each project gets its own manager
            doc_manager = ProjectDocumentLifecycle.initialize(project_root)

            # List documents for this specific project
            documents = doc_manager.registry.list_documents()
            self.logger.info(
                "project_documents",
                project=project_root.name,
                count=len(documents)
            )

            # Process documents for this project
            for doc in documents:
                self.process_document(project_root, doc)
```

**Checking Initialization**:

```python
def ensure_lifecycle(self, project_root: Path):
    """Ensure document lifecycle is initialized."""
    if not ProjectDocumentLifecycle.is_initialized(project_root):
        # Initialize if needed
        self.logger.info("initializing_lifecycle", project=project_root)

    # Initialize or get existing (idempotent)
    doc_manager = ProjectDocumentLifecycle.initialize(project_root)
    return doc_manager
```

### Best Practices for Project-Scoped Plugins

1. **Always Use Project Root**: Pass `project_root` parameter to all document operations
   ```python
   # Good: Project-specific
   doc_manager = ProjectDocumentLifecycle.initialize(project_root)

   # Bad: Assumes global
   doc_manager = DocumentLifecycle.get_instance()  # Don't do this!
   ```

2. **Check Initialization**: Always verify lifecycle is initialized before operations
   ```python
   if not ProjectDocumentLifecycle.is_initialized(project_root):
       ProjectDocumentLifecycle.initialize(project_root)
   ```

3. **Handle Failures Gracefully**: Lifecycle initialization can fail
   ```python
   try:
       doc_manager = ProjectDocumentLifecycle.initialize(project_root)
   except Exception as e:
       self.logger.error("lifecycle_init_failed", project=project_root, error=str(e))
       return None
   ```

4. **Project Isolation**: Never mix data between projects
   ```python
   # Good: Isolated per project
   for project in projects:
       manager = ProjectDocumentLifecycle.initialize(project)
       process_documents(manager)

   # Bad: Shared state across projects
   global_manager = get_global_manager()  # Don't do this!
   ```

5. **Metadata Tagging**: Tag plugin-created documents for identification
   ```python
   doc_manager.registry.register_document(
       path="docs/custom.md",
       doc_type="custom",
       metadata={
           "plugin": self.name,
           "version": self.version,
           "created_at": datetime.now().isoformat()
       }
   )
   ```

### Example: Document Generator Plugin

```python
from pathlib import Path
from gao_dev.lifecycle.project_lifecycle import ProjectDocumentLifecycle
from gao_dev.plugins import BasePlugin

class DocumentGeneratorPlugin(BasePlugin):
    """Plugin that generates custom documentation."""

    def generate_report(self, project_root: Path):
        """Generate a report document."""
        # Ensure lifecycle is ready
        doc_manager = self.ensure_lifecycle(project_root)
        if not doc_manager:
            return

        # Generate report content
        report_path = project_root / "docs" / "CUSTOM_REPORT.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text("# Custom Report\n\n...")

        # Register in lifecycle
        doc_manager.registry.register_document(
            path="docs/CUSTOM_REPORT.md",
            doc_type="custom-report",
            metadata={
                "plugin": "document-generator",
                "generator_version": "1.0.0"
            }
        )

        self.logger.info(
            "report_generated",
            project=project_root.name,
            path=str(report_path)
        )

    def ensure_lifecycle(self, project_root: Path):
        """Ensure lifecycle is initialized."""
        if not ProjectDocumentLifecycle.is_initialized(project_root):
            try:
                return ProjectDocumentLifecycle.initialize(project_root)
            except Exception as e:
                self.logger.error(
                    "lifecycle_init_failed",
                    project=project_root.name,
                    error=str(e)
                )
                return None
        return ProjectDocumentLifecycle.initialize(project_root)
```

### Common Patterns

**Pattern 1: Document Validator**

```python
def validate_documents(self, project_root: Path):
    """Validate all documents in a project."""
    doc_manager = ProjectDocumentLifecycle.initialize(project_root)
    documents = doc_manager.registry.list_documents()

    for doc in documents:
        if not (project_root / doc.path).exists():
            self.logger.warning("missing_document", path=doc.path)
```

**Pattern 2: Document Analyzer**

```python
def analyze_documentation(self, project_root: Path):
    """Analyze documentation completeness."""
    doc_manager = ProjectDocumentLifecycle.initialize(project_root)
    documents = doc_manager.registry.list_documents()

    doc_types = {}
    for doc in documents:
        doc_types[doc.doc_type] = doc_types.get(doc.doc_type, 0) + 1

    return {
        "project": project_root.name,
        "total_documents": len(documents),
        "by_type": doc_types
    }
```

**Pattern 3: Cross-Project Report**

```python
def generate_cross_project_report(self, project_roots: List[Path]):
    """Generate report across multiple projects."""
    report = []

    for project_root in project_roots:
        if not ProjectDocumentLifecycle.is_initialized(project_root):
            continue

        doc_manager = ProjectDocumentLifecycle.initialize(project_root)
        documents = doc_manager.registry.list_documents()

        report.append({
            "project": project_root.name,
            "document_count": len(documents),
            "types": list(set(d.doc_type for d in documents))
        })

    return report
```

---

## Best Practices

### Code Organization

```
my_plugin/
  __init__.py           # Package marker
  plugin.yaml          # Plugin metadata
  agent.py             # Agent implementation
  agent_plugin.py      # Plugin implementation
  helpers.py           # Helper functions
  config.py            # Configuration handling
  tests/               # Test suite
    __init__.py
    test_agent.py
    test_plugin.py
  README.md            # Documentation
  requirements.txt     # Dependencies
```

### Naming Conventions

- **Plugin Name**: `kebab-case` (my-custom-plugin)
- **Python Modules**: `snake_case` (my_plugin)
- **Classes**: `PascalCase` (MyAgentPlugin)
- **Functions**: `snake_case` (execute_task)

### Error Handling

```python
# Good: Specific error handling
try:
    result = await risky_operation()
except FileNotFoundError:
    yield "File not found - please check path"
    return
except PermissionDeniedError:
    yield "Permission denied - check plugin.yaml"
    return
except Exception as e:
    yield f"Unexpected error: {e}"
    raise

# Bad: Catching everything silently
try:
    result = await risky_operation()
except:
    pass  # Silent failure
```

### Logging

```python
import structlog

logger = structlog.get_logger(__name__)

# Good: Structured logging
logger.info(
    "task_started",
    task_id=task.id,
    agent=self.name
)

# Bad: String formatting
print(f"Task {task.id} started by {self.name}")
```

### Performance

- **Async/Await**: Use async for I/O operations
- **Caching**: Cache expensive computations
- **Lazy Loading**: Load resources only when needed
- **Resource Cleanup**: Always cleanup in finally blocks

---

## Troubleshooting

### Plugin Not Discovered

**Symptoms**: Plugin doesn't appear in `gao-dev list-plugins`

**Common Causes**:
1. Missing `__init__.py` in plugin directory
2. Missing or invalid `plugin.yaml`
3. Plugin directory not in configured paths
4. Plugin name conflicts with existing plugin

**Solutions**:
```bash
# Check plugin structure
ls my_plugin/
# Should show: __init__.py, plugin.yaml, agent.py, agent_plugin.py

# Validate plugin.yaml
gao-dev validate-plugin my_plugin/

# Check plugin directories
gao-dev config show | grep plugin_directories

# Enable debug logging
export GAO_DEV_LOG_LEVEL=DEBUG
gao-dev load-plugins
```

### Plugin Load Errors

**Symptoms**: Plugin discovered but fails to load

**Common Causes**:
1. Invalid entry point in plugin.yaml
2. Missing dependencies
3. Syntax errors in plugin code
4. Invalid permissions in plugin.yaml

**Solutions**:
```bash
# Check entry point format
# Correct:   my_plugin.agent_plugin.MyAgentPlugin
# Incorrect: my_plugin/agent_plugin.py:MyAgentPlugin

# Install dependencies
pip install -r my_plugin/requirements.txt

# Validate Python syntax
python -m py_compile my_plugin/*.py

# Check permission format
# Correct:   file:read
# Incorrect: FILE_READ, read_file
```

### Permission Denied Errors

**Symptoms**: `PermissionDeniedError` at runtime

**Cause**: Plugin attempting operation without permission

**Solution**: Add required permission to plugin.yaml:

```yaml
permissions:
  - file:write  # Add this if writing files
```

### Timeout Errors

**Symptoms**: `PluginTimeoutError` during initialization

**Causes**:
1. Slow initialization (network calls, large file loads)
2. Infinite loop in initialize()
3. Timeout too short

**Solutions**:
```yaml
# Increase timeout in plugin.yaml
timeout_seconds: 60

# Or optimize initialization
def initialize(self):
    # Move slow operations to first use
    self._data = None  # Load later
    return True

async def execute_task(self, task, context):
    if self._data is None:
        self._data = await load_data()  # Lazy load
```

---

## API Reference

### BasePlugin

**Methods**:

- `initialize() -> bool`: Called after loading (optional)
- `cleanup() -> None`: Called before unload (optional)
- `register_hooks() -> None`: Register lifecycle hooks (optional)
- `unregister_hooks() -> None`: Unregister hooks (automatic)

### BaseAgentPlugin

**Extends**: BasePlugin

**Abstract Methods** (must implement):

- `get_agent_class() -> Type[IAgent]`: Return agent class
- `get_agent_name() -> str`: Return unique agent name
- `get_agent_metadata() -> AgentMetadata`: Return metadata

### BaseWorkflowPlugin

**Extends**: BasePlugin

**Abstract Methods** (must implement):

- `get_workflow_class() -> Type[IWorkflow]`: Return workflow class
- `get_workflow_identifier() -> WorkflowIdentifier`: Return identifier
- `get_workflow_metadata() -> WorkflowMetadata`: Return metadata

### HookManager

**Methods**:

- `register_hook(event_type, handler, priority=100, name=None, plugin_name=None)`: Register hook
- `unregister_hook(event_type, handler) -> bool`: Unregister specific hook
- `execute_hooks(event_type, event_data) -> HookResults`: Execute all hooks for event

### PluginSandbox

**Methods**:

- `validate_plugin(metadata) -> ValidationResult`: Validate plugin
- `check_permission(plugin_name, operation) -> bool`: Check permission
- `enforce_permission(plugin_name, operation)`: Enforce permission (raises if denied)
- `execute_with_timeout(func, timeout_seconds, *args, **kwargs)`: Execute with timeout

---

## Additional Resources

- **Example Plugins**: `tests/plugins/fixtures/`
- **Plugin Template**: `examples/plugin-template/`
- **API Documentation**: `docs/api/`
- **Community Forums**: https://github.com/anthropics/gao-dev/discussions
- **Issue Tracker**: https://github.com/anthropics/gao-dev/issues

---

**Happy Plugin Development!** 🚀
