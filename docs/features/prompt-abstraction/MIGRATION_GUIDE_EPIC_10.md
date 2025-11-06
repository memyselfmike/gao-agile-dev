# Migration Guide: Epic 10 - Prompt & Agent Configuration Abstraction

This guide helps you migrate from hardcoded prompts and agent configurations to the new YAML-based abstraction system introduced in Epic 10.

## Overview

Epic 10 introduces a complete abstraction layer for prompts and agent configurations, moving all hardcoded strings into structured YAML files for better maintainability and customization.

## What Changed

### 1. Prompt Templates (Stories 10.1-10.6)

**Before (Hardcoded):**
```python
# In orchestrator.py
task = f"""Use the John agent to create a Product Requirements Document for '{project_name}'.

John should:
1. Use the 'prd' workflow to understand the structure
2. Create a comprehensive PRD.md file
...
"""
```

**After (YAML-based):**
```yaml
# gao_dev/prompts/tasks/create_prd.yaml
name: create_prd
description: "Task prompt for PRD creation by John"
version: 1.0.0

user_prompt: |
  Use the John agent to create a Product Requirements Document for '{{project_name}}'.

  John should:
  1. Use the 'prd' workflow to understand the structure
  2. Create a comprehensive PRD.md file
  ...

variables:
  project_name: ""
  agent: "John"
```

```python
# In orchestrator.py
template = self.prompt_loader.load_prompt("tasks/create_prd")
task = self.prompt_loader.render_prompt(template, {"project_name": project_name})
```

### 2. Agent Configurations (Stories 10.1-10.3)

**Before (Hardcoded):**
```python
# In agent_definitions.py
builtin_agents = {
    "mary": {
        "name": "Mary",
        "role": "Engineering Manager",
        "tools": ["Read", "Write"]
    }
}
```

**After (YAML-based):**
```yaml
# gao_dev/agents/mary.agent.yaml
agent:
  metadata:
    name: Mary
    role: Engineering Manager
  tools:
    - Read
    - Write
```

### 3. Plugin System Enhancements (Story 10.7)

Plugins can now provide custom agents and prompts via YAML:

```python
class MyPlugin(BaseAgentPlugin):
    def get_agent_definitions(self) -> List[AgentConfig]:
        return [AgentConfig.from_yaml(Path("agents/custom.agent.yaml"))]

    def get_prompt_templates(self) -> List[PromptTemplate]:
        return [PromptTemplate.from_yaml(Path("prompts/custom.yaml"))]
```

## Migration Steps

### For Custom Agents

If you have custom agent implementations:

#### Step 1: Create Agent Definition YAML

Create `agents/my_agent.agent.yaml`:

```yaml
agent:
  metadata:
    name: MyAgent
    role: Custom Role
    description: "Description of what this agent does"
    version: 1.0.0

  persona:
    background: |
      You are MyAgent, specialized in...

    responsibilities:
      - Responsibility 1
      - Responsibility 2

    communication_style: "Professional and concise"

  capabilities:
    - capability_1
    - capability_2

  tools:
    - Read
    - Write
    - Grep

  configuration:
    model: "claude-sonnet-4-5-20250929"
    max_tokens: 4000
    temperature: 0.7
```

#### Step 2: Load Agent Configuration

```python
from gao_dev.core.models.agent_config import AgentConfig
from pathlib import Path

agent_config = AgentConfig.from_yaml(Path("agents/my_agent.agent.yaml"))
```

#### Step 3: Remove Hardcoded Configuration

Remove dictionary-based agent definitions from Python code.

### For Custom Prompts

If you have hardcoded prompts in your code:

#### Step 1: Extract Prompt to YAML

Create `prompts/my_prompt.yaml`:

```yaml
name: my_prompt
description: "Description of this prompt"
version: 1.0.0

system_prompt: |
  You are {{agent_name}}...

user_prompt: |
  Your task is to {{task_description}}.

  Steps:
  1. {{step_1}}
  2. {{step_2}}

variables:
  agent_name: ""
  task_description: ""
  step_1: ""
  step_2: ""

response:
  max_tokens: 4000
  temperature: 0.7

metadata:
  category: custom
  phase: processing
```

#### Step 2: Load and Render Prompt

```python
from gao_dev.core.prompt_loader import PromptLoader
from pathlib import Path

loader = PromptLoader(
    prompts_dir=Path("prompts"),
    cache_enabled=True
)

template = loader.load_prompt("my_prompt")
rendered = loader.render_prompt(template, {
    "agent_name": "MyAgent",
    "task_description": "Process the data",
    "step_1": "Load data",
    "step_2": "Transform data"
})
```

#### Step 3: Remove Hardcoded Strings

Delete f-strings and hardcoded prompt text from Python code.

### For Plugin Developers

If you're creating plugins:

#### Step 1: Implement New Plugin Methods

```python
from gao_dev.plugins.agent_plugin import BaseAgentPlugin
from pathlib import Path

class MyPlugin(BaseAgentPlugin):
    def get_agent_definitions(self) -> List[AgentConfig]:
        """Load agent definitions from YAML files."""
        plugin_dir = Path(__file__).parent
        configs = []

        for yaml_file in (plugin_dir / "agents").glob("*.agent.yaml"):
            configs.append(AgentConfig.from_yaml(yaml_file))

        return configs

    def get_prompt_templates(self) -> List[PromptTemplate]:
        """Load prompt templates from YAML files."""
        plugin_dir = Path(__file__).parent
        templates = []

        for yaml_file in (plugin_dir / "prompts").glob("*.yaml"):
            templates.append(PromptTemplate.from_yaml(yaml_file))

        return templates
```

#### Step 2: Structure Plugin Directory

```
my-plugin/
├── plugin.yaml
├── my_plugin.py
├── agents/
│   ├── agent1.agent.yaml
│   └── agent2.agent.yaml
└── prompts/
    ├── prompt1.yaml
    └── prompt2.yaml
```

#### Step 3: Use Plugin Manager

```python
from gao_dev.plugins.agent_plugin_manager import AgentPluginManager

# Load agent definitions from plugins
configs = plugin_manager.load_agent_definitions_from_plugins()

# Load prompt templates from plugins
templates = plugin_manager.load_prompt_templates_from_plugins()
```

## Reference Resolution

The new system supports reference resolution for dynamic content:

### File References

Load content from files:

```yaml
variables:
  responsibilities: "@file:common/responsibilities/developer.md"
```

### Config References

Load values from configuration:

```yaml
variables:
  model: "@config:claude_model"
  max_tokens: "@config:max_tokens"
```

## Breaking Changes

### None for v1.x

Epic 10 maintains **100% backwards compatibility** for version 1.x:

- Existing code continues to work without changes
- Hardcoded prompts are migrated but old code paths remain
- Deprecated features will be removed in v2.0 (future)

### Planned for v2.0 (Future)

The following will be removed in version 2.0:

1. Hardcoded agent dictionaries in Python
2. Hardcoded prompts in code
3. Direct string-based prompt construction

## Benefits of Migration

### 1. Maintainability
- All prompts in one place
- Easy to update without code changes
- Version control for prompts

### 2. Customization
- Override prompts via configuration
- Plugin system for extensions
- No code changes needed

### 3. Testability
- Validate YAML schemas
- Test prompts independently
- Mock prompt loading

### 4. Reusability
- Share prompts across projects
- Create prompt libraries
- Plugin ecosystem

## Validation

After migration, validate your setup:

### 1. Run Health Check

```bash
gao-dev health
```

Should show:
- All agent definitions loaded
- All prompt templates valid
- No schema validation errors

### 2. Run Tests

```bash
pytest tests/
```

All tests should pass without changes.

### 3. Verify Functionality

```python
# Test agent configuration loading
from gao_dev.core.models.agent_config import AgentConfig
config = AgentConfig.from_yaml(Path("agents/mary.agent.yaml"))
assert config.metadata.name == "Mary"

# Test prompt loading and rendering
from gao_dev.core.prompt_loader import PromptLoader
loader = PromptLoader(prompts_dir=Path("prompts"))
template = loader.load_prompt("tasks/create_prd")
rendered = loader.render_prompt(template, {"project_name": "Test"})
assert "Test" in rendered
```

## Performance Impact

Epic 10 has **minimal performance impact**:

- **Prompt loading**: <5% overhead (with caching enabled)
- **Agent initialization**: No measurable difference
- **Runtime execution**: Identical performance

Caching is enabled by default, so prompts are loaded once and reused.

## Troubleshooting

### Schema Validation Errors

If you see schema validation errors:

```
SchemaValidationError: Prompt validation failed for 'my_prompt'
```

**Solution**: Check your YAML syntax and ensure all required fields are present.

### Prompt Not Found

If you see:

```
PromptNotFoundError: Prompt 'my_prompt' not found
```

**Solution**: Verify the file exists at the expected location and the name matches.

### Reference Resolution Errors

If you see:

```
ReferenceResolutionError: File not found: common/file.md
```

**Solution**: Check that referenced files exist and paths are correct (relative to prompts directory or project root).

## Example: Complete Migration

### Before (Hardcoded)

```python
# In orchestrator.py
async def create_feature(self, feature_name: str):
    task = f"""Use the Amelia agent to implement {feature_name}.

    Steps:
    1. Create feature file
    2. Write tests
    3. Implement functionality
    4. Commit changes
    """
    async for message in self.execute_task(task):
        yield message
```

### After (YAML-based)

**1. Create prompt YAML:**

```yaml
# prompts/tasks/create_feature.yaml
name: create_feature
description: "Task prompt for feature implementation"
version: 1.0.0

user_prompt: |
  Use the Amelia agent to implement {{feature_name}}.

  Steps:
  1. Create feature file
  2. Write tests
  3. Implement functionality
  4. Commit changes

variables:
  feature_name: ""
  agent: "Amelia"

response:
  max_tokens: 4000
  temperature: 0.7
```

**2. Update Python code:**

```python
# In orchestrator.py
async def create_feature(self, feature_name: str):
    template = self.prompt_loader.load_prompt("tasks/create_feature")
    task = self.prompt_loader.render_prompt(template, {"feature_name": feature_name})

    async for message in self.execute_task(task):
        yield message
```

## Support

For questions or issues:

1. Check [Plugin Development Guide](plugin-development-guide.md)
2. Review [Agent Configuration Reference](agent-configuration.md)
3. See [Prompt Template Reference](prompt-templates.md)
4. Open an issue on GitHub

## Related Documentation

- [Epic 10 Architecture](features/prompt-abstraction/ARCHITECTURE.md)
- [Plugin Development Guide](plugin-development-guide.md)
- [Agent Configuration Schema](schemas/agent-config.schema.json)
- [Prompt Template Schema](schemas/prompt-template.schema.json)
