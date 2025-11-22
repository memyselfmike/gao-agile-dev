# Developer Guide: Adding Agents to GAO-Dev

## TL;DR

**What**: Step-by-step guide to creating new autonomous agents in the GAO-Dev system

**When**: Adding new specialized capabilities (e.g., security auditor, performance optimizer, deployment manager)

**Key Steps**:
1. Create agent configuration YAML (`gao_dev/config/agents/`)
2. Write persona document (`gao_dev/config/agents/personas/`)
3. Register agent with orchestrator
4. Add CLI commands (optional)
5. Update web UI (optional)
6. Test agent execution

**Time**: 2-4 hours for basic agent, 1-2 days for fully integrated agent

---

## Table of Contents

- [Overview](#overview)
- [Agent Architecture](#agent-architecture)
- [Step-by-Step Guide](#step-by-step-guide)
- [Agent Configuration Schema](#agent-configuration-schema)
- [Persona Definition](#persona-definition)
- [Integration](#integration)
- [Testing](#testing)
- [Example: Diana (Document Keeper)](#example-diana-document-keeper)
- [Common Patterns](#common-patterns)

---

## Overview

### What is an Agent?

In GAO-Dev, an **agent** is an autonomous AI persona with:
- **Specialized role** and responsibilities
- **Unique capabilities** and skills
- **Configuration** defining behavior and constraints
- **Persona** defining communication style and decision-making
- **Tools** and workflows available to them

### Current Agents (9 Specialized)

| Agent | Role | Primary Responsibilities |
|-------|------|--------------------------|
| **Brian** | Workflow Coordinator | Workflow selection, scale routing, orchestration |
| **Mary** | Business Analyst | Requirements, brainstorming, vision elicitation |
| **John** | Product Manager | PRDs, feature definition, prioritization |
| **Winston** | Technical Architect | Architecture, technical specifications, design |
| **Sally** | UX Designer | User experience, wireframes, design systems |
| **Bob** | Scrum Master | Story management, sprint coordination, ceremonies |
| **Amelia** | Software Developer | Implementation, code reviews, testing |
| **Murat** | Test Architect | Test strategies, quality assurance, automation |
| **Diana** | Document Keeper | Documentation, knowledge architecture, guides |

---

## Agent Architecture

### Components of an Agent

```
gao_dev/config/agents/
├── {agent-name}.yaml        # Agent configuration (required)
└── personas/
    └── {agent-name}.md      # Persona definition (required)

gao_dev/cli/
└── {agent-name}_commands.py # CLI commands (optional)

gao_dev/web/frontend/src/
└── components/agents/
    └── {AgentName}View.tsx  # Web UI integration (optional)
```

### Agent Lifecycle

```
1. Configuration → 2. Registration → 3. Invocation → 4. Execution → 5. Output
```

---

## Step-by-Step Guide

### Step 1: Create Agent Configuration

**File**: `gao_dev/config/agents/your_agent.yaml`

```yaml
# Your Agent Configuration
# Specialized Agent: Your Agent Description

agent:
  name: "YourAgent"
  role: "Your Agent Role"
  type: "your-agent-type"  # e.g., "documentation", "security", "performance"
  emoji: "🔧"  # Agent emoji for UI
  color: "#FF5722"  # Hex color for UI theme

description: |
  Brief description of what this agent does and why it's valuable.
  Explain the agent's primary purpose and how it fits into GAO-Dev.

responsibilities:
  - Primary responsibility 1
  - Primary responsibility 2
  - Primary responsibility 3

capabilities:
  - Capability 1 (what agent can do)
  - Capability 2
  - Capability 3

persona_file: "gao_dev/config/agents/personas/your_agent.md"

tools:
  - "read_file"
  - "write_file"
  - "edit_file"
  - "bash_command"
  - "git_commit"
  # Add tools your agent needs

workflows:
  primary:
    - "workflow-1"
    - "workflow-2"
  specialized:
    - "specialized-workflow-1"

metrics:
  - "Metric 1 to track agent performance"
  - "Metric 2"

collaboration:
  with_brian: "How this agent collaborates with Brian"
  with_winston: "How this agent collaborates with Winston"
  # Add collaboration patterns with other agents

command_prefix: "your-cmd"  # For CLI commands: gao-dev your-cmd <action>

available_commands:
  - name: "action1"
    description: "What this command does"
    usage: "gao-dev your-cmd action1 <args>"

version: "1.0"
created: "2025-01-16"
status: "active"
```

### Step 2: Create Persona Document

**File**: `gao_dev/config/agents/personas/your_agent.md`

```markdown
# YourAgent - Your Agent Role Persona

## Core Identity

You are **YourAgent**, the Your Agent Role for the GAO-Dev autonomous development team.

Your mission: **[One-sentence mission statement]**

## Your Role

As the [Role Title], you:

1. **Primary Responsibility** - [Description]
2. **Secondary Responsibility** - [Description]
3. **Tertiary Responsibility** - [Description]

## Personality Traits

### [Trait 1]
[Description of how this trait manifests in the agent's behavior]

### [Trait 2]
[Description]

### [Trait 3]
[Description]

## Communication Style

### With Users
- **[Style 1]**: [Description]
- **[Style 2]**: [Description]

### With Other Agents
- **[Style 1]**: [Description]
- **[Style 2]**: [Description]

### Writing Style
- **[Principle 1]**: [Description]
- **[Principle 2]**: [Description]

## Core Principles (Your Beliefs)

### The [Principle Name] Principle
> "[Quote describing the principle]"

[Explanation of what this means in practice]

## Your Workflow

### When [Performing Primary Task]

1. **[Step 1]**
   - [Substep 1]
   - [Substep 2]

2. **[Step 2]**
   - [Substep 1]
   - [Substep 2]

## Decision-Making Framework

### When to [Decision Point 1]

**Do when**:
- ✅ [Condition 1]
- ✅ [Condition 2]

**Don't when**:
- ❌ [Condition 1]
- ❌ [Condition 2]

## Quality Standards

**Required**:
- ✅ [Standard 1]
- ✅ [Standard 2]

## Collaboration Patterns

### With [Other Agent]
- **You provide**: [What you give them]
- **They provide**: [What they give you]
- **Together**: [What you achieve together]

## Success Metrics

**You measure success by**:
- [Metric 1]: [How measured]
- [Metric 2]: [How measured]

## Remember

- [Key principle 1]
- [Key principle 2]
- [Key principle 3]

**Your work is critical because [reason].**

---

**Version**: 1.0
**Created**: 2025-01-16
**Role**: [Agent Role]
```

### Step 3: Register Agent with Orchestrator

**File**: `gao_dev/orchestrator/gao_dev_orchestrator.py`

```python
# Add agent to agent registry (if manual registration needed)
# Most agents auto-register from config files

from gao_dev.agents.your_agent import YourAgent

class GAODevOrchestrator:
    def __init__(self):
        # ... existing init ...

        # Register your agent
        self.agents["your_agent"] = YourAgent(
            config=self.config_loader.load_agent_config("your_agent")
        )
```

**Note**: Modern GAO-Dev uses auto-discovery from YAML configs. Manual registration only needed for special cases.

### Step 4: Add CLI Commands (Optional)

**File**: `gao_dev/cli/your_agent_commands.py`

```python
"""CLI commands for YourAgent."""
import click
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


@click.group(name="your-cmd")
def your_agent_cli():
    """YourAgent commands."""
    pass


@your_agent_cli.command("action1")
@click.argument("target")
@click.option("--option1", help="Optional parameter")
def action1(target: str, option1: str | None):
    """Perform action1 on target.

    Args:
        target: Target for action
        option1: Optional parameter
    """
    logger.info("performing_action1", target=target, option1=option1)

    # Import orchestrator and execute agent workflow
    from gao_dev.orchestrator import GAODevOrchestrator

    orchestrator = GAODevOrchestrator()
    result = orchestrator.execute_agent_task(
        agent_name="your_agent",
        task="action1",
        params={"target": target, "option1": option1}
    )

    if result.success:
        click.echo(f"✅ Action1 completed successfully")
    else:
        click.echo(f"❌ Action1 failed: {result.error}", err=True)


# Register with main CLI
def register_commands(cli):
    """Register YourAgent commands with main CLI.

    Args:
        cli: Main Click CLI group
    """
    cli.add_command(your_agent_cli)
```

**File**: `gao_dev/cli/__init__.py`

```python
# Add import and registration
from .your_agent_commands import register_commands as register_your_agent_commands

def create_cli():
    """Create main CLI."""
    # ... existing setup ...

    # Register your agent commands
    register_your_agent_commands(cli)

    return cli
```

### Step 5: Update Web UI (Optional)

**File**: `gao_dev/web/frontend/src/types/index.ts`

```typescript
// Add agent to Agent type
export interface Agent {
  id: string;
  name: string;
  role: string;
  status: 'active' | 'inactive';
  color: string;
  emoji: string;
}

// Your agent will be added to the agents list
export const AGENTS: Agent[] = [
  // ... existing agents ...
  {
    id: 'your_agent',
    name: 'YourAgent',
    role: 'Your Agent Role',
    status: 'active',
    color: '#FF5722',
    emoji: '🔧',
  },
];
```

**File**: `gao_dev/web/api/agents.py` (if exists)

```python
# Agent metadata endpoint will auto-discover from config
# No manual changes needed if using config-based discovery
```

### Step 6: Test Your Agent

**File**: `tests/agents/test_your_agent.py`

```python
"""Tests for YourAgent."""
import pytest
from pathlib import Path
from gao_dev.agents.your_agent import YourAgent


@pytest.fixture
def your_agent(tmp_path):
    """Create test agent instance."""
    config = {
        "name": "YourAgent",
        "role": "Your Agent Role",
        "tools": ["read_file", "write_file"],
    }
    return YourAgent(config=config, project_root=tmp_path)


def test_your_agent_initialization(your_agent):
    """Test agent initializes correctly."""
    assert your_agent.name == "YourAgent"
    assert your_agent.role == "Your Agent Role"


def test_your_agent_performs_task(your_agent, tmp_path):
    """Test agent can perform its primary task."""
    result = your_agent.execute_task(
        task_name="action1",
        params={"target": "test-target"}
    )

    assert result.success
    assert result.output is not None
```

---

## Agent Configuration Schema

### Complete Schema

```yaml
# Agent Metadata
agent:
  name: string              # Agent display name (PascalCase)
  role: string              # Agent role description
  type: string              # Agent type category
  emoji: string             # Unicode emoji for UI
  color: string             # Hex color (#RRGGBB) for UI theming

# Description
description: |              # Multi-line agent description
  What the agent does
  Why it's valuable
  How it fits into GAO-Dev

# Responsibilities
responsibilities:           # List of agent responsibilities
  - string
  - string

# Capabilities
capabilities:               # List of agent capabilities
  - string
  - string

# Persona
persona_file: string        # Path to persona markdown file

# Tools
tools:                      # List of tool names agent can use
  - string
  - string

# Workflows
workflows:                  # Workflows agent can execute
  primary:                  # Primary workflows
    - string
    - string
  specialized:              # Specialized/advanced workflows
    - string
    - string

# Quality Standards (optional)
quality_standards:          # Agent-specific quality standards
  category1:
    - string
    - string
  category2:
    - string

# Metrics (optional)
metrics:                    # Success metrics for agent
  - string
  - string

# Collaboration (optional)
collaboration:              # How agent collaborates with others
  with_agent_name: string   # Collaboration description

# CLI Integration (optional)
command_prefix: string      # Prefix for CLI commands
available_commands:         # List of CLI commands
  - name: string           # Command name
    description: string    # Command description
    usage: string         # Usage example

# Output Formats (optional)
output_formats:             # Agent-specific output formats
  format_name:
    max_tokens: integer
    required_sections:
      - string
      - string

# Agent Interaction Patterns (optional)
agent_interaction_patterns:
  when_to_invoke_agent:    # When to invoke this agent
    - string
    - string
  agent_invokes_others:    # When this agent invokes others
    - string
    - string

# Metadata
version: string            # Version (semantic versioning)
created: string           # Creation date (YYYY-MM-DD)
last_updated: string      # Last update date (YYYY-MM-DD)
status: string            # Status: active, inactive, deprecated
```

---

## Persona Definition

### Persona Template Structure

```markdown
# [Agent Name] - [Role] Persona

## Core Identity
[Who the agent is, their mission]

## Your Role
[What they do, their responsibilities]

## Personality Traits
[How they behave, their characteristics]

## Communication Style
[How they interact with users and other agents]

## Core Principles
[Their beliefs and decision-making framework]

## Your Workflow
[How they approach tasks step-by-step]

## Decision-Making Framework
[When to do what, guidelines for choices]

## Quality Standards
[What standards they maintain]

## Collaboration Patterns
[How they work with other agents]

## Success Metrics
[How they measure their effectiveness]

## Remember
[Key takeaways and reminders]
```

### Best Practices for Personas

1. **Be Specific**: Define clear, actionable behaviors
2. **Show Personality**: Give agent unique voice and style
3. **Include Examples**: Show decision-making in practice
4. **Define Boundaries**: Be clear about what agent does and doesn't do
5. **Enable Collaboration**: Explain how to work with other agents

---

## Integration

### Auto-Discovery

Modern GAO-Dev uses config-based auto-discovery:

```python
# gao_dev/core/config_loader.py
class ConfigLoader:
    def discover_agents(self) -> Dict[str, dict]:
        """Auto-discover agents from config directory."""
        agents = {}

        agent_configs = Path("gao_dev/config/agents").glob("*.yaml")
        for config_file in agent_configs:
            if config_file.stem == "personas":
                continue  # Skip personas directory

            agent_config = yaml.safe_load(config_file.read_text())
            agents[config_file.stem] = agent_config

        return agents
```

### Manual Registration (Legacy)

If needed, manually register in orchestrator:

```python
from gao_dev.agents.base import BaseAgent

class YourAgent(BaseAgent):
    """Your agent implementation."""

    def __init__(self, config: dict, project_root: Path):
        super().__init__(config, project_root)
        self.setup_tools()

    async def execute_task(self, task_name: str, params: dict) -> TaskResult:
        """Execute agent task."""
        # Implementation here
        pass
```

---

## Testing

### Unit Tests

```python
"""tests/agents/test_your_agent.py"""
import pytest
from gao_dev.agents.your_agent import YourAgent


class TestYourAgent:
    """Test suite for YourAgent."""

    def test_initialization(self, tmp_path):
        """Test agent initializes correctly."""
        config = {...}
        agent = YourAgent(config, tmp_path)

        assert agent.name == "YourAgent"
        assert len(agent.tools) > 0

    def test_primary_task_execution(self, tmp_path):
        """Test agent can execute primary task."""
        agent = YourAgent({...}, tmp_path)
        result = agent.execute_task("primary_task", {})

        assert result.success
        assert result.output is not None

    def test_error_handling(self, tmp_path):
        """Test agent handles errors gracefully."""
        agent = YourAgent({...}, tmp_path)
        result = agent.execute_task("invalid_task", {})

        assert not result.success
        assert result.error is not None
```

### Integration Tests

```python
"""tests/integration/test_your_agent_integration.py"""
from gao_dev.orchestrator import GAODevOrchestrator


def test_agent_orchestrator_integration(tmp_path):
    """Test agent works with orchestrator."""
    orchestrator = GAODevOrchestrator(project_root=tmp_path)

    result = orchestrator.execute_agent_task(
        agent_name="your_agent",
        task="action1",
        params={"target": "test"}
    )

    assert result.success
```

---

## Example: Diana (Document Keeper)

Diana is a complete example of adding a new agent. She was added as the 9th specialized agent in GAO-Dev.

### Key Files

1. **Configuration**: `gao_dev/config/agents/diana.yaml` (225 lines)
2. **Persona**: `gao_dev/config/agents/personas/diana.md` (470 lines)
3. **CLI Integration**: Slash commands in `.claude/commands/doc-*.md`
4. **Skills**: `.claude/skills/documentation/SKILL.md`

### What Makes Diana a Good Example

- **Complete configuration**: All optional fields demonstrated
- **Rich persona**: Clear personality, principles, workflows
- **Quality standards**: Specific, measurable standards defined
- **Collaboration patterns**: Shows how to work with all other agents
- **CLI commands**: 10 specialized commands
- **Output formats**: Defined structures for different document types

### Studying Diana

```bash
# Read Diana's configuration
cat gao_dev/config/agents/diana.yaml

# Read Diana's persona
cat gao_dev/config/agents/personas/diana.md

# See Diana's commands
ls .claude/commands/doc-*.md

# Review documentation skill
cat .claude/skills/documentation/SKILL.md
```

---

## Common Patterns

### Pattern 1: Analysis Agent

Agents that analyze code/docs/metrics:

```yaml
agent:
  type: "analysis"
  tools:
    - "read_file"
    - "grep"
    - "glob"
    - "static_analysis_tool"

workflows:
  primary:
    - "code-analysis"
    - "metrics-analysis"
```

### Pattern 2: Creation Agent

Agents that create artifacts:

```yaml
agent:
  type: "creation"
  tools:
    - "write_file"
    - "edit_file"
    - "git_commit"

workflows:
  primary:
    - "document-creation"
    - "code-generation"
```

### Pattern 3: Coordination Agent

Agents that coordinate other agents:

```yaml
agent:
  type: "coordination"
  tools:
    - "workflow_executor"
    - "agent_invoker"

collaboration:
  coordinates:
    - "agent1"
    - "agent2"
    - "agent3"
```

### Pattern 4: Quality Agent

Agents that ensure quality:

```yaml
agent:
  type: "quality"
  tools:
    - "test_runner"
    - "linter"
    - "code_reviewer"

quality_standards:
  coverage_threshold: 80
  max_complexity: 10
```

---

## See Also

- [Agent Factory Implementation](../../gao_dev/core/factories/agent_factory.py) - Agent creation code
- [Base Agent Interface](../../gao_dev/core/interfaces/agent.py) - Agent interface definition
- [Diana Configuration](../../gao_dev/config/agents/diana.yaml) - Complete agent example
- [CLAUDE.md](../../CLAUDE.md) - All 9 agents overview

**Estimated tokens**: ~2,400
