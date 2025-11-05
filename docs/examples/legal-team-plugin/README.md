# Legal Team Plugin Example

This example demonstrates how to create a custom agent plugin for GAO-Dev that provides domain-specific agents and prompts.

## Overview

The Legal Team Plugin provides:
- **Laura** - Legal Analyst agent specializing in contract review and compliance
- **Contract Review Prompt** - Structured prompt for legal document analysis

## Plugin Structure

```
legal-team-plugin/
├── plugin.yaml                    # Plugin metadata
├── legal_plugin.py                # Plugin implementation
├── agents/
│   └── laura.agent.yaml          # Laura agent definition
├── prompts/
│   └── contract_review.yaml      # Contract review prompt template
└── README.md                      # This file
```

## Installation

### 1. Copy Plugin to Plugins Directory

```bash
# Copy plugin to GAO-Dev plugins directory
cp -r legal-team-plugin ~/.gao-dev/plugins/legal-team-plugin

# Or for development
ln -s /path/to/legal-team-plugin ~/.gao-dev/plugins/legal-team-plugin
```

### 2. Enable Plugin

Edit `~/.gao-dev/config.yaml`:

```yaml
plugins:
  enabled: true
  directories:
    - ~/.gao-dev/plugins

  # Optional: Explicitly enable plugins
  enabled_plugins:
    - legal-team-plugin
```

### 3. Verify Installation

```bash
gao-dev list-agents
# Should show Laura in the list

gao-dev health
# Should show plugin loaded successfully
```

## Usage

### Using Laura Agent

```python
from gao_dev.orchestrator import GAODevOrchestrator

# Create orchestrator
orchestrator = GAODevOrchestrator.create_default(
    project_root=Path.cwd(),
    api_key="your-api-key"
)

# Use Laura for contract review
async for message in orchestrator.execute_task(
    "Use Laura to review the contract at docs/contracts/vendor-agreement.pdf"
):
    print(message)
```

### Using Contract Review Prompt

```python
from gao_dev.core.prompt_loader import PromptLoader
from pathlib import Path

# Initialize prompt loader
loader = PromptLoader(
    prompts_dir=Path("~/.gao-dev/plugins/legal-team-plugin/prompts")
)

# Load and render prompt
template = loader.load_prompt("contract_review")
prompt = loader.render_prompt(template, {
    "contract_type": "Vendor Agreement",
    "parties": "Company A and Company B",
    "contract_path": "docs/contracts/vendor-agreement.pdf"
})

# Use with any agent
async for message in orchestrator.execute_task(prompt):
    print(message)
```

## Plugin Implementation Details

### 1. Agent Definition (laura.agent.yaml)

Defines Laura's configuration:
- Metadata (name, role, description)
- Persona and responsibilities
- Capabilities and tools
- Workflow preferences
- LLM configuration

### 2. Prompt Template (contract_review.yaml)

Structured prompt for contract review with:
- System prompt (sets agent context)
- User prompt (task instructions)
- Variables for customization
- Response configuration

### 3. Plugin Class (legal_plugin.py)

Implements `BaseAgentPlugin` interface:

```python
class LegalTeamPlugin(BaseAgentPlugin):
    def get_agent_class(self) -> Type[IAgent]:
        return ClaudeAgent  # Use built-in ClaudeAgent

    def get_agent_name(self) -> str:
        return "Laura"

    def get_agent_metadata(self) -> AgentMetadata:
        return AgentMetadata(...)

    def get_agent_definitions(self) -> List[AgentConfig]:
        # Load YAML agent definitions
        return [AgentConfig.from_yaml(...)]

    def get_prompt_templates(self) -> List[PromptTemplate]:
        # Load YAML prompt templates
        return [PromptTemplate.from_yaml(...)]
```

## Extending the Plugin

### Add More Agents

1. Create agent definition YAML in `agents/`
2. Update `get_agent_definitions()` to load it
3. Optionally create custom agent class

### Add More Prompts

1. Create prompt template YAML in `prompts/`
2. Update `get_prompt_templates()` to load it
3. Use with any agent via PromptLoader

### Custom Agent Implementation

```python
from gao_dev.agents.base import BaseAgent

class CustomLegalAgent(BaseAgent):
    async def execute_task(self, task, context):
        # Custom implementation
        yield "Custom agent processing..."
        # Your logic here
        yield "Task complete"

class LegalTeamPlugin(BaseAgentPlugin):
    def get_agent_class(self):
        return CustomLegalAgent  # Use custom class
```

## Best Practices

1. **Agent Definitions**: Use YAML for configuration, code for logic
2. **Prompt Templates**: Keep prompts in YAML for easy editing
3. **Versioning**: Use semantic versioning for plugin and templates
4. **Testing**: Test plugin in isolation before deployment
5. **Documentation**: Provide clear README and usage examples

## Troubleshooting

### Plugin Not Loading

```bash
# Check plugin status
gao-dev health

# Enable debug logging
export GAO_DEV_LOG_LEVEL=DEBUG
gao-dev list-agents
```

### Agent Not Available

1. Verify plugin.yaml has correct metadata
2. Check plugin is enabled in config
3. Ensure agent YAML is valid
4. Review logs for errors

### Prompt Not Found

1. Verify prompt YAML exists in prompts/
2. Check prompt name matches file name
3. Ensure PromptLoader is configured correctly

## Related Documentation

- [Plugin Development Guide](../../plugin-development-guide.md)
- [Agent Configuration Reference](../../agent-configuration.md)
- [Prompt Template Reference](../../prompt-templates.md)
- [Plugin API Reference](../../api/plugins.md)

## License

MIT License - see LICENSE file for details
