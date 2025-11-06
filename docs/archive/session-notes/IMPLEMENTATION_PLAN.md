# Implementation Plan - GAO-Dev POC

**Project:** GAO-Dev - Software Engineering Team for Generative Autonomous Organisation
**Timeline:** 1 week (10-12 hours development)
**Approach:** Phased implementation with continuous testing
**Status:** Ready to execute

---

## Quick Reference

### Phase Overview
1. **Foundation** (2 hours) - Project structure, embedded assets
2. **Core Services** (2 hours) - Business logic layer
3. **SDK Tools** (1 hour) - Pure SDK tool layer
4. **Orchestrator** (2 hours) - Agent management and coordination
5. **CLI** (0.5 hours) - Command-line interface
6. **Testing** (2 hours) - Comprehensive test suite
7. **Integration** (1 hour) - End-to-end validation

**Total:** ~10.5 hours development time

---

## Phase 1: Foundation Setup (2 hours)

### Objective
Create project structure and embed all workflow assets

### Tasks

#### 1.1 Create Python Package Structure
```bash
# Create directory structure
mkdir -p gao_dev/{core,tools,orchestrator,cli,config,workflows,agents,checklists}
mkdir -p tests examples docs

# Create __init__.py files
touch gao_dev/__init__.py
touch gao_dev/{core,tools,orchestrator,cli}/__init__.py
```

**Files to create:**
- `pyproject.toml` - Package configuration
- `gao_dev/__init__.py` - Package root
- `gao_dev/__version__.py` - Version info

#### 1.2 Copy and Adapt Workflows
```bash
# Copy from BMAD MCP handoff-docs source
# Workflows are in D:\BMAD MCP (source material location)
```

**Source:** Reference workflows from BMAD-METHOD patterns
**Destination:** `gao_dev/workflows/`
**Structure:**
```
gao_dev/workflows/
├── 0-meta/
│   └── workflow-status/
├── 1-analysis/
│   ├── product-brief/
│   ├── research/
│   └── document-project/
├── 2-plan/
│   ├── prd/
│   ├── tech-spec-sm/
│   └── brainstorm-project/
├── 3-solutioning/
│   ├── architecture/
│   ├── create-ux-design/
│   └── solutioning-gate-check/
└── 4-implementation/
    ├── create-story/
    ├── story-context/
    ├── story-ready/
    ├── dev-story/
    ├── review-story/
    └── story-done/
```

**Each workflow needs:**
- `workflow.yaml` - Metadata (name, phase, variables, etc.)
- `instructions.md` - Agent instructions
- `template.md` - Output template
- `checklist.md` (optional) - Quality checklist

#### 1.3 Copy Agent Personas
**Source:** Reference agent definitions from source materials
**Destination:** `gao_dev/agents/`

**Agents to create:**
- `mary.md` - Business Analyst
- `john.md` - Product Manager
- `winston.md` - Technical Architect
- `sally.md` - UX Designer
- `bob.md` - Scrum Master
- `amelia.md` - Software Developer
- `murat.md` - Test Architect

#### 1.4 Copy Quality Checklists
**Destination:** `gao_dev/checklists/`

**Checklists:**
- `qa-comprehensive.md` - Master checklist
- `clean-architecture.md`
- `solid-principles.md`
- `type-safety.md`
- `tdd.md`
- `logging.md`
- `error-handling.md`
- `documentation.md`

#### 1.5 Create Default Configuration
**File:** `gao_dev/config/defaults.yaml`

```yaml
# Default GAO-Dev configuration
output_folder: "docs"
dev_story_location: "docs/stories"
context_xml_folder: "docs/stories/{epic}/context"
git_auto_commit: true
git_branch_prefix: "feature/epic"
qa_enabled: true
test_coverage_threshold: 80
log_level: "INFO"
```

**Deliverable:** Complete project structure with embedded assets

---

## Phase 2: Core Services (2 hours)

### Objective
Implement core business logic services

### Services to Implement

#### 2.1 Models (`gao_dev/core/models.py`)
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

@dataclass
class WorkflowInfo:
    """Workflow metadata."""
    name: str
    description: str
    phase: int
    installed_path: Path
    author: Optional[str]
    tags: List[str]
    variables: Dict[str, Any]
    required_tools: List[str]
    interactive: bool
    autonomous: bool
    iterative: bool
    web_bundle: bool

class StoryStatus(Enum):
    """Story status enum."""
    DRAFT = "draft"
    READY = "ready"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    DONE = "done"

class HealthStatus(Enum):
    """Health check status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class CheckResult:
    """Individual health check result."""
    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    remediation: Optional[str] = None
```

#### 2.2 ConfigLoader (`gao_dev/core/config_loader.py`)
Manages configuration with defaults and user overrides.

**Key methods:**
- `__init__(project_root: Path)`
- `get(key: str, default: Any = None) -> Any`
- `get_workflows_path() -> Path` (points to embedded)
- `get_agents_path() -> Path` (points to embedded)
- `get_checklists_path() -> Path` (points to embedded)

#### 2.3 WorkflowRegistry (`gao_dev/core/workflow_registry.py`)
Discovers and indexes workflows.

**Key methods:**
- `index_workflows() -> None`
- `get_workflow(name: str) -> Optional[WorkflowInfo]`
- `list_workflows(phase: Optional[int] = None) -> List[WorkflowInfo]`
- `get_all_workflows() -> Dict[str, WorkflowInfo]`

#### 2.4 WorkflowExecutor (`gao_dev/core/workflow_executor.py`)
Executes workflows with variable resolution and template rendering.

**Key methods:**
- `execute(workflow: WorkflowInfo, params: Dict[str, Any]) -> Dict[str, Any]`
- `_resolve_variables(workflow: WorkflowInfo, params: Dict[str, Any]) -> Dict[str, Any]`
- `_render_template(template: str, variables: Dict[str, Any]) -> str`

#### 2.5 StateManager (`gao_dev/core/state_manager.py`)
Manages story and workflow state.

**Key methods:**
- `get_story_status(epic: int, story: int) -> Optional[str]`
- `set_story_status(epic: int, story: int, status: str) -> bool`
- `update_workflow_status(workflow_name: str, status: str) -> bool`
- `get_sprint_status() -> Dict[str, Any]`

#### 2.6 GitManager (`gao_dev/core/git_manager.py`)
Handles git operations.

**Key methods:**
- `git_init() -> bool`
- `git_add(files: List[str]) -> bool`
- `git_commit(message: str) -> bool`
- `git_branch(branch_name: str) -> bool`
- `git_merge(branch_name: str) -> bool`
- `create_conventional_commit(type: str, scope: str, description: str) -> str`

#### 2.7 AgentRegistry (`gao_dev/core/agent_registry.py`)
Discovers and loads agent personas.

**Key methods:**
- `index_agents() -> None`
- `get_agent(name: str) -> Optional[str]`
- `list_agents() -> List[str]`

#### 2.8 HealthCheck (`gao_dev/core/health_check.py`)
Validates system configuration and state.

**Key methods:**
- `run_all_checks() -> Dict[str, Any]`
- `check_project_structure() -> CheckResult`
- `check_workflows() -> CheckResult`
- `check_git() -> CheckResult`
- `check_configuration() -> CheckResult`

**Deliverable:** All core services implemented and unit tested

---

## Phase 3: Pure SDK Tools (1 hour)

### Objective
Create @tool decorated functions for Claude Agent SDK

### File: `gao_dev/tools/gao_tools.py`

#### Tools to Implement (10-15 tools)

```python
from claude_agent_sdk import tool
from pathlib import Path
from typing import Optional, Dict, Any, List

# Module-level initialization
config = ConfigLoader(Path.cwd())
registry = WorkflowRegistry(config)
state_manager = StateManager(config)
git_manager = GitManager(config)
agent_registry = AgentRegistry(config)
health_checker = HealthCheck(config)

@tool(name="list_workflows")
async def list_workflows(phase: Optional[int] = None) -> Dict[str, Any]:
    """List available GAO-Dev workflows."""
    pass

@tool(name="get_workflow")
async def get_workflow(workflow_name: str) -> Dict[str, Any]:
    """Get detailed workflow information."""
    pass

@tool(name="execute_workflow")
async def execute_workflow(
    workflow_name: str,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute a GAO-Dev workflow."""
    pass

@tool(name="get_story_status")
async def get_story_status(epic: int, story: int) -> Dict[str, Any]:
    """Get status of a story."""
    pass

@tool(name="set_story_status")
async def set_story_status(epic: int, story: int, status: str) -> Dict[str, Any]:
    """Set status of a story."""
    pass

@tool(name="git_commit")
async def git_commit(files: List[str], message: str) -> Dict[str, Any]:
    """Create git commit."""
    pass

@tool(name="git_create_branch")
async def git_create_branch(branch_name: str) -> Dict[str, Any]:
    """Create git branch."""
    pass

@tool(name="git_merge_branch")
async def git_merge_branch(branch_name: str) -> Dict[str, Any]:
    """Merge git branch."""
    pass

@tool(name="health_check")
async def health_check(format: str = "json") -> Dict[str, Any]:
    """Run system health check."""
    pass

@tool(name="list_agents")
async def list_agents() -> Dict[str, Any]:
    """List available agent personas."""
    pass

@tool(name="get_agent_persona")
async def get_agent_persona(agent_name: str) -> Dict[str, Any]:
    """Get agent persona definition."""
    pass

@tool(name="read_file")
async def read_file(file_path: str) -> Dict[str, Any]:
    """Read file contents."""
    pass

@tool(name="write_file")
async def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """Write file contents."""
    pass

@tool(name="list_stories")
async def list_stories(epic: Optional[int] = None) -> Dict[str, Any]:
    """List stories for an epic or all stories."""
    pass

@tool(name="get_sprint_status")
async def get_sprint_status() -> Dict[str, Any]:
    """Get current sprint status."""
    pass
```

#### Export Tools (`gao_dev/tools/__init__.py`)
```python
from .gao_tools import (
    list_workflows,
    get_workflow,
    execute_workflow,
    get_story_status,
    set_story_status,
    git_commit,
    git_create_branch,
    git_merge_branch,
    health_check,
    list_agents,
    get_agent_persona,
    read_file,
    write_file,
    list_stories,
    get_sprint_status,
)

__all__ = [
    "list_workflows",
    "get_workflow",
    "execute_workflow",
    "get_story_status",
    "set_story_status",
    "git_commit",
    "git_create_branch",
    "git_merge_branch",
    "health_check",
    "list_agents",
    "get_agent_persona",
    "read_file",
    "write_file",
    "list_stories",
    "get_sprint_status",
]
```

**Deliverable:** 10-15 Pure SDK tools ready for agent use

---

## Phase 4: Orchestrator (2 hours)

### Objective
Build agent management and workflow orchestration

#### 4.1 AgentManager (`gao_dev/orchestrator/agent_manager.py`)

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from pathlib import Path
from typing import AsyncGenerator
from ..tools import *

class AgentManager:
    """Spawn and manage GAO-Dev agents."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.tools = [
            list_workflows,
            get_workflow,
            execute_workflow,
            get_story_status,
            set_story_status,
            git_commit,
            git_create_branch,
            git_merge_branch,
            health_check,
            list_agents,
            get_agent_persona,
            read_file,
            write_file,
            list_stories,
            get_sprint_status,
        ]

    async def spawn_agent(
        self,
        persona_name: str,
        task: str
    ) -> AsyncGenerator[str, None]:
        """Spawn agent with GAO-Dev tools and persona."""
        persona = self._load_persona(persona_name)

        options = ClaudeAgentOptions(
            tools=self.tools,
            system_prompt=persona
        )

        async with ClaudeSDKClient(options=options) as agent:
            async for message in agent.query(task):
                yield message

    def _load_persona(self, persona_name: str) -> str:
        """Load agent persona from embedded agents."""
        agents_path = Path(__file__).parent.parent / "agents"
        persona_file = agents_path / f"{persona_name}.md"
        return persona_file.read_text(encoding="utf-8")
```

#### 4.2 WorkflowEngine (`gao_dev/orchestrator/workflow_engine.py`)

```python
class WorkflowEngine:
    """Execute GAO-Dev workflows autonomously."""

    def __init__(self, agent_manager: AgentManager):
        self.agent_manager = agent_manager

    async def execute_story_workflow(
        self,
        epic: int,
        story: int
    ) -> AsyncGenerator[str, None]:
        """Execute complete story workflow."""

        # 1. Create story (Scrum Master)
        async for msg in self.agent_manager.spawn_agent(
            "bob",
            f"Create Story {epic}.{story} using the create-story workflow"
        ):
            yield f"[Bob/SM] {msg}"

        # 2. Generate context (Scrum Master)
        async for msg in self.agent_manager.spawn_agent(
            "bob",
            f"Generate context for Story {epic}.{story} using story-context workflow"
        ):
            yield f"[Bob/SM] {msg}"

        # 3. Mark ready (Scrum Master)
        async for msg in self.agent_manager.spawn_agent(
            "bob",
            f"Mark Story {epic}.{story} as Ready using story-ready workflow"
        ):
            yield f"[Bob/SM] {msg}"

        # 4. Implement story (Developer)
        async for msg in self.agent_manager.spawn_agent(
            "amelia",
            f"Implement Story {epic}.{story} using dev-story workflow"
        ):
            yield f"[Amelia/Dev] {msg}"

        # 5. Review story (Developer)
        async for msg in self.agent_manager.spawn_agent(
            "amelia",
            f"Review Story {epic}.{story} using review-story workflow"
        ):
            yield f"[Amelia/Dev] {msg}"

        # 6. Mark done (Scrum Master)
        async for msg in self.agent_manager.spawn_agent(
            "bob",
            f"Mark Story {epic}.{story} as Done using story-done workflow"
        ):
            yield f"[Bob/SM] {msg}"
```

#### 4.3 Coordination Service (`gao_dev/orchestrator/coordination.py`)
Basic multi-agent coordination (for POC, keep simple).

**Deliverable:** Agent orchestration working end-to-end

---

## Phase 5: CLI Interface (0.5 hours)

### Objective
Create command-line interface with Click

### File: `gao_dev/cli/commands.py`

```python
import click
import asyncio
from pathlib import Path
from ..orchestrator import AgentManager, WorkflowEngine
from ..core import ConfigLoader, HealthCheck

@click.group()
@click.version_option(version="1.0.0")
def cli():
    """GAO-Dev - Autonomous AI Development Team."""
    pass

@cli.command()
@click.option("--name", default="My Project", help="Project name")
def init(name: str):
    """Initialize a new GAO-Dev project."""
    click.echo(f"Initializing GAO-Dev project: {name}")
    # Create project structure
    # Create gao-dev.yaml
    # Run health check
    click.echo("✓ Project initialized successfully!")

@cli.command()
@click.argument("workflow_name")
@cli.option("--param", "-p", multiple=True, help="Workflow parameters (key=value)")
def execute(workflow_name: str, param: tuple):
    """Execute a workflow."""
    click.echo(f"Executing workflow: {workflow_name}")
    # Parse params
    # Execute workflow
    click.echo("✓ Workflow completed!")

@cli.command()
@click.option("--epic", type=int, required=True, help="Epic number")
@click.option("--story", type=int, required=True, help="Story number")
def create_story(epic: int, story: int):
    """Create a new user story."""
    click.echo(f"Creating Story {epic}.{story}")

    async def run():
        manager = AgentManager(Path.cwd())
        task = f"Create Story {epic}.{story}"
        async for message in manager.spawn_agent("bob", task):
            click.echo(message)

    asyncio.run(run())
    click.echo("✓ Story created!")

@cli.command()
@click.option("--epic", type=int, required=True, help="Epic number")
@click.option("--story", type=int, required=True, help="Story number")
def implement_story(epic: int, story: int):
    """Implement a user story (full workflow)."""
    click.echo(f"Implementing Story {epic}.{story}")

    async def run():
        manager = AgentManager(Path.cwd())
        engine = WorkflowEngine(manager)
        async for message in engine.execute_story_workflow(epic, story):
            click.echo(message)

    asyncio.run(run())
    click.echo("✓ Story implementation complete!")

@cli.command()
@click.option("--format", type=click.Choice(["json", "markdown"]), default="markdown")
def health(format: str):
    """Run health check."""
    config = ConfigLoader(Path.cwd())
    checker = HealthCheck(config)
    result = checker.run_all_checks()

    if format == "json":
        import json
        click.echo(json.dumps(result, indent=2))
    else:
        # Pretty print markdown
        click.echo("# GAO-Dev Health Check\n")
        for check in result["checks"]:
            status_icon = "✓" if check["status"] == "healthy" else "⚠" if check["status"] == "warning" else "✗"
            click.echo(f"{status_icon} {check['name']}: {check['message']}")

@cli.command()
@click.option("--phase", type=int, help="Filter by phase")
def list_workflows(phase: int):
    """List available workflows."""
    # List workflows
    click.echo("Available workflows:")

@cli.command()
def list_agents():
    """List available agent personas."""
    # List agents
    click.echo("Available agents:")

if __name__ == "__main__":
    cli()
```

### Entry Point
Update `pyproject.toml`:
```toml
[project.scripts]
gao-dev = "gao_dev.cli.commands:cli"
```

**Deliverable:** Working CLI with all commands

---

## Phase 6: Testing (2 hours)

### Objective
Achieve 80%+ test coverage

### Test Structure

#### 6.1 Core Service Tests
```
tests/
├── test_models.py
├── test_config_loader.py
├── test_workflow_registry.py
├── test_workflow_executor.py
├── test_state_manager.py
├── test_git_manager.py
├── test_agent_registry.py
└── test_health_check.py
```

#### 6.2 Tool Tests
```
tests/
├── test_tools.py
└── test_tool_integration.py
```

#### 6.3 Orchestrator Tests
```
tests/
├── test_agent_manager.py
└── test_workflow_engine.py
```

#### 6.4 Integration Tests
```
tests/
└── test_integration.py
    ├── test_complete_story_workflow
    ├── test_health_check_integration
    └── test_cli_commands
```

### Test Configuration (`tests/conftest.py`)
```python
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def temp_project():
    """Create temporary project structure."""
    temp_dir = Path(tempfile.mkdtemp())
    # Create structure
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config():
    """Mock configuration."""
    pass

@pytest.fixture
def sample_workflow():
    """Sample workflow for testing."""
    pass
```

**Deliverable:** 80%+ test coverage, all tests passing

---

## Phase 7: Integration & Validation (1 hour)

### Objective
End-to-end testing and final validation

### Integration Tests

#### 7.1 Complete Story Workflow Test
```python
@pytest.mark.asyncio
async def test_complete_story_workflow(temp_project):
    """Test end-to-end story creation and implementation."""
    # Initialize project
    # Create story
    # Generate context
    # Implement story
    # Mark done
    # Verify all artifacts created
    pass
```

#### 7.2 CLI Integration Test
```bash
# Test all CLI commands
gao-dev --version
gao-dev init --name "Test Project"
gao-dev health
gao-dev list-workflows
gao-dev list-agents
gao-dev create-story --epic 1 --story 1
```

#### 7.3 Health Check Validation
```python
def test_health_check_full_validation():
    """Test health check catches all issues."""
    # Test various broken states
    # Verify remediation messages
    pass
```

**Deliverable:** Fully integrated and tested POC

---

## Package Configuration

### pyproject.toml (Complete)

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "gao-dev"
version = "1.0.0"
description = "GAO-Dev - Software Engineering Team for Generative Autonomous Organisation"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "GAO Development Team"}
]
keywords = ["ai", "agents", "autonomous", "development", "gao"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "claude-agent-sdk>=1.0.0",
    "pyyaml>=6.0",
    "gitpython>=3.1.0",
    "click>=8.1.0",
    "structlog>=23.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=23.10.0",
    "ruff>=0.1.0",
    "mypy>=1.6.0",
    "types-PyYAML",
]

[project.scripts]
gao-dev = "gao_dev.cli.commands:cli"

[project.urls]
Homepage = "https://github.com/gao-org/gao-dev"
Documentation = "https://github.com/gao-org/gao-dev#readme"
Repository = "https://github.com/gao-org/gao-dev"
Issues = "https://github.com/gao-org/gao-dev/issues"

[tool.setuptools]
packages = ["gao_dev"]

[tool.setuptools.package-data]
gao_dev = [
    "workflows/**/*",
    "agents/*",
    "checklists/*",
    "config/*",
]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=gao_dev --cov-report=html --cov-report=term"
asyncio_mode = "auto"
```

---

## Success Criteria

### POC Complete When:

- [ ] All 7 phases completed
- [ ] Project structure created
- [ ] 34+ workflows embedded
- [ ] 7 agent personas embedded
- [ ] Core services implemented (8 services)
- [ ] 15 Pure SDK tools implemented
- [ ] Orchestrator working (AgentManager + WorkflowEngine)
- [ ] CLI functional (8+ commands)
- [ ] Tests passing (80%+ coverage)
- [ ] Can execute: `gao-dev init`
- [ ] Can execute: `gao-dev health`
- [ ] Can execute: `gao-dev create-story --epic 1 --story 1`
- [ ] Can execute: `gao-dev implement-story --epic 1 --story 1`
- [ ] Complete story workflow works end-to-end
- [ ] Git integration working
- [ ] Health checks passing
- [ ] Documentation complete (README.md)

---

## Risk Mitigation

### Common Issues & Solutions

**Issue:** Claude Agent SDK not available
**Solution:** Mock SDK for testing, document requirement

**Issue:** Workflow discovery fails
**Solution:** Add extensive logging, provide fallback

**Issue:** Agent coordination breaks
**Solution:** Add retry logic, state recovery

**Issue:** Git operations fail
**Solution:** Defensive error handling, clear messages

**Issue:** Tests don't reach 80% coverage
**Solution:** Focus on critical paths, add integration tests

---

## Development Commands

### Setup Development Environment
```bash
cd "D:\GAO Agile Dev"
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest
pytest --cov=gao_dev --cov-report=html
```

### Code Quality
```bash
black gao_dev tests
ruff check gao_dev tests
mypy gao_dev
```

### Build Package
```bash
python -m build
pip install dist/gao_dev-*.whl
```

### Test Installation
```bash
gao-dev --version
gao-dev --help
```

---

## Next Steps After POC

1. **Gather Feedback** - Test with real projects
2. **Performance Tuning** - Optimize agent spawn time
3. **Enhanced Logging** - Better observability
4. **Web UI** - Browser-based monitoring
5. **Cloud Deployment** - Deploy agents to cloud
6. **Community Workflows** - Allow custom workflows
7. **Advanced Features** - SQLite state, E2E testing, CI/CD integration

---

**Document Owner:** GAO Development Team
**Last Updated:** 2025-10-27
**Status:** Ready to Execute
