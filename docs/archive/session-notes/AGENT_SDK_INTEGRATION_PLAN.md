# GAO-Dev - Claude Agent SDK Integration Plan

**Date:** 2025-10-27
**Goal:** Properly integrate Claude Agent SDK for fully autonomous agent execution
**Status:** Planning

---

## Current State Analysis

### ✅ What We Have
1. **Project Structure**: Complete package structure with workflows, agents, config
2. **CLI Interface**: Working commands for init, health, list-workflows, execute
3. **Core Services**: Workflow registry, executor, state manager, git manager
4. **Documentation**: Comprehensive PRD, implementation plan, README
5. **Embedded Assets**: 3 workflows, 3 agent personas, quality checklists

### ❌ What's Missing
1. **Actual Agent SDK Integration**: No real agent spawning or autonomous execution
2. **Custom Tools**: No `@tool` decorated functions for agents to use
3. **SDK MCP Server**: No MCP server wrapping our tools
4. **Agent Definitions**: No proper `AgentDefinition` configuration
5. **Autonomous Execution**: Workflows just return instructions, don't actually execute

---

## Key Learnings from SDK Examples

### From `claude-agent-sdk-intro`:

1. **Tool Creation Pattern** (Module 2):
```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("tool_name", "Description", {"param": type})
async def my_tool(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{
            "type": "text",
            "text": "Result"
        }]
    }

# Create MCP server
server = create_sdk_mcp_server(
    name="server_name",
    version="1.0.0",
    tools=[my_tool]
)
```

2. **Agent Configuration** (Module 3):
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    model="claude-sonnet-4",
    mcp_servers={"server_name": server},
    allowed_tools=["Read", "Write", "mcp__server_name__tool_name"],
    system_prompt="Custom instructions..."
)
```

3. **Subagents** (Module 6):
```python
from claude_agent_sdk import AgentDefinition

options = ClaudeAgentOptions(
    model="claude-sonnet-4",
    agents={
        "developer": AgentDefinition(
            description="Developer agent",
            prompt="You are a developer...",
            model="sonnet",
            tools=["Read", "Write", "Edit", ...]
        )
    },
    allowed_tools=["Task"]  # Required for spawning subagents
)
```

4. **Execution Pattern**:
```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("Do the task")

    async for message in client.receive_response():
        # Process messages
        pass
```

### From `big-3-super-agent`:

1. **Working Directory Management**: Agents work in a specific directory
2. **Session Management**: Track agent sessions in registry files
3. **Tool-Based Orchestration**: Main agent calls tools to spawn/manage sub-agents
4. **uv for Environment**: Use `uv` for package management and script execution

---

## Integration Architecture

### Layer 1: Custom Tools (MCP Server)

**File**: `gao_dev/tools/gao_tools.py`

Create tools that agents can use:
```python
from claude_agent_sdk import tool, create_sdk_mcp_server
from typing import Any

@tool("list_workflows", "List available GAO-Dev workflows", {"phase": int})
async def list_workflows(args: dict[str, Any]) -> dict[str, Any]:
    # Implementation using WorkflowRegistry
    pass

@tool("execute_workflow", "Execute a workflow", {"name": str, "params": dict})
async def execute_workflow(args: dict[str, Any]) -> dict[str, Any]:
    # Implementation using WorkflowExecutor
    pass

@tool("create_story", "Create a user story", {"epic": int, "story": int})
async def create_story(args: dict[str, Any]) -> dict[str, Any]:
    # Implementation using StateManager
    pass

@tool("update_story_status", "Update story status", {"epic": int, "story": int, "status": str})
async def update_story_status(args: dict[str, Any]) -> dict[str, Any]:
    # Implementation
    pass

@tool("git_commit", "Create git commit", {"files": list, "message": str})
async def git_commit(args: dict[str, Any]) -> dict[str, Any]:
    # Implementation using GitManager
    pass

# Create MCP server
gao_dev_server = create_sdk_mcp_server(
    name="gao_dev",
    version="1.0.0",
    tools=[
        list_workflows,
        execute_workflow,
        create_story,
        update_story_status,
        git_commit,
        # ... all tools
    ]
)
```

### Layer 2: Agent Definitions

**File**: `gao_dev/orchestrator/agent_definitions.py`

```python
from claude_agent_sdk import AgentDefinition
from pathlib import Path

def load_agent_persona(agent_name: str) -> str:
    """Load agent persona from embedded agents."""
    agents_path = Path(__file__).parent.parent / "agents"
    persona_file = agents_path / f"{agent_name}.md"
    return persona_file.read_text(encoding="utf-8")

# Bob - Scrum Master
bob_agent = AgentDefinition(
    description="Scrum Master who creates and manages user stories",
    prompt=load_agent_persona("bob"),
    model="sonnet",
    tools=[
        "Read",
        "Write",
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__create_story",
        "mcp__gao_dev__update_story_status",
    ]
)

# Amelia - Developer
amelia_agent = AgentDefinition(
    description="Software developer who implements stories",
    prompt=load_agent_persona("amelia"),
    model="sonnet",
    tools=[
        "Read",
        "Write",
        "Edit",
        "MultiEdit",
        "Bash",
        "mcp__gao_dev__execute_workflow",
        "mcp__gao_dev__update_story_status",
        "mcp__gao_dev__git_commit",
    ]
)

# John - Product Manager
john_agent = AgentDefinition(
    description="Product Manager who creates PRDs and defines features",
    prompt=load_agent_persona("john"),
    model="sonnet",
    tools=[
        "Read",
        "Write",
        "mcp__gao_dev__list_workflows",
        "mcp__gao_dev__execute_workflow",
    ]
)

AGENT_DEFINITIONS = {
    "bob": bob_agent,
    "amelia": amelia_agent,
    "john": john_agent,
}
```

### Layer 3: Orchestrator

**File**: `gao_dev/orchestrator/orchestrator.py`

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from pathlib import Path
from typing import AsyncGenerator
from ..tools.gao_tools import gao_dev_server
from .agent_definitions import AGENT_DEFINITIONS

class GAODevOrchestrator:
    """Main orchestrator for GAO-Dev autonomous agents."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

        # Configure main orchestrator options
        self.options = ClaudeAgentOptions(
            model="claude-sonnet-4",
            mcp_servers={"gao_dev": gao_dev_server},
            agents=AGENT_DEFINITIONS,
            allowed_tools=[
                "Read",
                "Write",
                "Edit",
                "Grep",
                "Glob",
                "Task",  # Required for spawning subagents
                "TodoWrite",
                "mcp__gao_dev__list_workflows",
                "mcp__gao_dev__execute_workflow",
                "mcp__gao_dev__create_story",
                "mcp__gao_dev__update_story_status",
                "mcp__gao_dev__git_commit",
            ],
            cwd=str(project_root),
            system_prompt=self._load_orchestrator_prompt()
        )

    def _load_orchestrator_prompt(self) -> str:
        """Load orchestrator system prompt."""
        return """
You are the GAO-Dev orchestrator, managing a team of specialized AI agents for software development.

Available agents:
- Bob (Scrum Master): Creates and manages user stories
- Amelia (Developer): Implements stories and writes code
- John (Product Manager): Creates PRDs and defines features

Your role:
1. Understand the user's request
2. Delegate to the appropriate specialist agent using the Task tool
3. Coordinate multi-agent workflows when needed
4. Ensure quality standards are met
5. Track progress and report status

Use the Task tool to spawn agents for their specific expertise.
"""

    async def execute_task(self, task: str) -> AsyncGenerator[str, None]:
        """Execute a task using the orchestrator."""
        async with ClaudeSDKClient(options=self.options) as client:
            await client.query(task)

            async for message in client.receive_response():
                # Parse and yield message
                if message.get("type") == "content_block_delta":
                    delta = message.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")

    async def create_story(self, epic: int, story: int) -> AsyncGenerator[str, None]:
        """Create a story using Bob (Scrum Master)."""
        task = f"Use the Bob agent to create Story {epic}.{story}"
        async for message in self.execute_task(task):
            yield message

    async def implement_story(self, epic: int, story: int) -> AsyncGenerator[str, None]:
        """Implement a story using full workflow."""
        task = f"""
Execute the complete story implementation workflow for Story {epic}.{story}:
1. Use Bob to verify the story is ready
2. Use Amelia to implement the story
3. Use Amelia to review and test
4. Use Bob to mark the story as done
"""
        async for message in self.execute_task(task):
            yield message

    async def create_prd(self, project_name: str) -> AsyncGenerator[str, None]:
        """Create PRD using John (PM)."""
        task = f"Use the John agent to create a PRD for '{project_name}'"
        async for message in self.execute_task(task):
            yield message
```

### Layer 4: CLI Integration

**File**: `gao_dev/cli/commands.py` (updated)

```python
import asyncio
from ..orchestrator.orchestrator import GAODevOrchestrator

@cli.command()
@click.option("--epic", type=int, required=True)
@click.option("--story", type=int, required=True)
def create_story(epic: int, story: int):
    """Create a user story autonomously."""
    project_root = Path.cwd()
    orchestrator = GAODevOrchestrator(project_root)

    click.echo(f">> Creating Story {epic}.{story} with Bob (Scrum Master)...\n")

    async def run():
        async for message in orchestrator.create_story(epic, story):
            click.echo(message, nl=False)

    asyncio.run(run())
    click.echo("\n\n[OK] Story creation complete!")

@cli.command()
@click.option("--epic", type=int, required=True)
@click.option("--story", type=int, required=True)
def implement_story(epic: int, story: int):
    """Implement a story autonomously (full workflow)."""
    project_root = Path.cwd()
    orchestrator = GAODevOrchestrator(project_root)

    click.echo(f">> Implementing Story {epic}.{story}...\n")

    async def run():
        async for message in orchestrator.implement_story(epic, story):
            click.echo(message, nl=False)

    asyncio.run(run())
    click.echo("\n\n[OK] Story implementation complete!")

@cli.command()
@click.option("--name", required=True)
def create_prd(name: str):
    """Create PRD autonomously."""
    project_root = Path.cwd()
    orchestrator = GAODevOrchestrator(project_root)

    click.echo(f">> Creating PRD with John (PM)...\n")

    async def run():
        async for message in orchestrator.create_prd(name):
            click.echo(message, nl=False)

    asyncio.run(run())
    click.echo("\n\n[OK] PRD creation complete!")
```

---

## Environment Setup with uv

### 1. Add uv support

**File**: `pyproject.toml` (update)

```toml
[project]
name = "gao-dev"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "claude-agent-sdk>=1.0.0",
    "pyyaml>=6.0",
    "gitpython>=3.1.0",
    "click>=8.1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.10.0",
    "ruff>=0.1.0",
]

[project.scripts]
gao-dev = "gao_dev.cli.commands:cli"
```

### 2. Setup Script

**File**: `setup.sh`

```bash
#!/bin/bash

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Sync dependencies
echo "Syncing dependencies..."
uv sync

echo "GAO-Dev setup complete!"
echo "Run: uv run gao-dev init"
```

---

## Implementation Phases

### Phase 1: Tool Layer (2-3 hours)
**Files**:
- `gao_dev/tools/gao_tools.py` - Custom tools
- `gao_dev/tools/tool_models.py` - Tool return type models

**Tasks**:
1. Convert existing service methods to `@tool` decorated functions
2. Create `create_sdk_mcp_server` with all tools
3. Implement proper return format (content blocks)
4. Test tools individually

### Phase 2: Agent Definitions (1 hour)
**Files**:
- `gao_dev/orchestrator/agent_definitions.py`
- Update agent personas with tool usage examples

**Tasks**:
1. Create `AgentDefinition` for each agent
2. Assign appropriate tools to each agent
3. Load personas from embedded files
4. Test agent configuration

### Phase 3: Orchestrator (2-3 hours)
**Files**:
- `gao_dev/orchestrator/orchestrator.py`
- `gao_dev/orchestrator/__init__.py`

**Tasks**:
1. Implement `GAODevOrchestrator` class
2. Configure `ClaudeAgentOptions`
3. Implement task execution methods
4. Add message parsing and streaming
5. Test orchestration

### Phase 4: CLI Integration (1 hour)
**Files**:
- Update `gao_dev/cli/commands.py`

**Tasks**:
1. Update commands to use orchestrator
2. Add async execution
3. Add progress indicators
4. Test all commands

### Phase 5: Environment & Testing (2 hours)
**Files**:
- `pyproject.toml`
- `setup.sh`
- `.env.sample`
- Test files

**Tasks**:
1. Add uv support
2. Create setup script
3. Test with uv run
4. End-to-end testing
5. Documentation updates

---

## Usage After Integration

### Setup
```bash
# Clone/navigate to project
cd gao-agile-dev

# Setup (installs uv if needed, syncs dependencies)
./setup.sh

# Or manually
uv sync
```

### Commands
```bash
# Initialize project
uv run gao-dev init --name "My Project"

# Create PRD (autonomous - John agent)
uv run gao-dev create-prd --name "My Project"

# Create story (autonomous - Bob agent)
uv run gao-dev create-story --epic 1 --story 1

# Implement story (autonomous - multi-agent)
uv run gao-dev implement-story --epic 1 --story 1

# Health check
uv run gao-dev health

# List workflows
uv run gao-dev list-workflows
```

---

## Success Criteria

### ✅ Properly Integrated When:

1. **Agents Actually Execute**: Not just returning instructions, but performing actions
2. **Tool Calls Work**: Agents can call GAO-Dev tools successfully
3. **Subagents Spawn**: Main orchestrator can spawn Bob, Amelia, John
4. **Workflows Complete**: Stories get created, implemented, and marked done autonomously
5. **Git Integration**: Commits are created automatically by agents
6. **File Operations**: Agents can read/write/edit files in the project
7. **Multi-Agent Coordination**: Bob → Amelia → Bob workflows execute smoothly
8. **uv Environment**: Everything runs via `uv run`

---

## Next Steps

1. **Review this plan** with you for approval
2. **Start Phase 1**: Implement tool layer
3. **Iteratively build** through phases 2-5
4. **Test thoroughly** at each phase
5. **Document** the autonomous capabilities
6. **Demo** end-to-end autonomous story implementation

---

## Questions to Resolve

1. **API Key vs Logged-in Session**: Which authentication method to use?
   - Option A: ANTHROPIC_API_KEY in .env
   - Option B: Use Claude Code logged-in session

2. **Working Directory**: Should agents be restricted to project root?

3. **Agent Permissions**: What file operations should be allowed/restricted?

4. **Error Handling**: How should we handle agent failures?

5. **State Persistence**: Should we track agent sessions like big-3-super-agent?

---

**Status**: Ready for your review and approval to proceed!
