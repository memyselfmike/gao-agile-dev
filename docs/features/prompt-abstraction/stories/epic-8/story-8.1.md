# Story 8.1: Agent Configuration Unification

**Epic**: 8 - Prompt & Agent Abstraction
**Story Points**: 5
**Priority**: High
**Status**: Pending
**Assignee**: TBD

---

## Story

**As a** developer
**I want** all agent configurations in declarative YAML format
**So that** I can add/modify agents without touching code

---

## Description

Migrate all 8 GAO-Dev agents from hardcoded Python dictionaries in `agent_factory.py` to declarative YAML files following the BMAD agent schema pattern (`bmad/bmm/agents/*.agent.yaml`).

This creates a single source of truth for agent configurations and eliminates duplicate definitions across the codebase.

---

## Acceptance Criteria

### 1. Agent YAML Files Created
- [ ] `gao_dev/agents/mary.agent.yaml` created
- [ ] `gao_dev/agents/john.agent.yaml` created
- [ ] `gao_dev/agents/winston.agent.yaml` created
- [ ] `gao_dev/agents/sally.agent.yaml` created
- [ ] `gao_dev/agents/bob.agent.yaml` created
- [ ] `gao_dev/agents/amelia.agent.yaml` created
- [ ] `gao_dev/agents/murat.agent.yaml` created
- [ ] `gao_dev/agents/brian.agent.yaml` created

### 2. AgentConfigLoader Implemented
- [ ] `gao_dev/core/agent_config_loader.py` created
- [ ] Can load agent from `.agent.yaml` file
- [ ] Can load persona from referenced `.md` file
- [ ] Validates required fields exist
- [ ] Returns AgentConfig dataclass

### 3. AgentConfig Data Model
- [ ] `gao_dev/core/models/agent_config.py` created
- [ ] AgentConfig dataclass with all required fields
- [ ] `from_yaml()` class method implemented
- [ ] `to_dict()` method implemented

### 4. AgentFactory Refactored
- [ ] `_register_builtin_agents()` uses AgentConfigLoader
- [ ] Hardcoded agent dictionaries removed
- [ ] Tool lists loaded from YAML
- [ ] Capabilities loaded from YAML

### 5. Zero Duplicate Configurations
- [ ] Agent tools defined only in YAML
- [ ] Agent metadata defined only in YAML
- [ ] No duplicate tool lists in code

### 6. All Tests Passing
- [ ] All existing agent tests pass
- [ ] New AgentConfigLoader tests added
- [ ] AgentFactory tests updated
- [ ] Integration tests verify same functionality

---

## Technical Details

### Current State (BEFORE)

**File**: `gao_dev/core/factories/agent_factory.py` (lines 20-90)
```python
def _register_builtin_agents(self) -> None:
    """Register all built-in GAO-Dev agents."""
    builtin_agents = {
        "mary": {
            "name": "Mary",
            "role": "Business Analyst",
            "tools": ["Read", "Write", "Grep", "Glob", "WebSearch", "WebFetch"],
            "capabilities": [CommonCapabilities.ANALYSIS]
        },
        "john": {
            "name": "John",
            "role": "Product Manager",
            "tools": ["Read", "Write", "Grep", "Glob"],
            "capabilities": [CommonCapabilities.PLANNING]
        },
        # ... 6 more agents (70+ lines)
    }
    self._agent_configs = builtin_agents
```

**Problems**:
- 70+ lines of hardcoded configuration
- Tools duplicated (also in `orchestrator/agent_definitions.py`)
- Can't modify without code changes
- No schema validation

### Target State (AFTER)

**File**: `gao_dev/agents/amelia.agent.yaml`
```yaml
agent:
  metadata:
    name: Amelia
    role: Software Developer
    icon: 💻
    version: 1.0.0

  persona_file: ./amelia.md

  tools:
    - Read
    - Write
    - Edit
    - MultiEdit
    - Bash
    - Grep
    - Glob
    - TodoWrite

  capabilities:
    - implementation
    - code_review
    - testing

  model: claude-sonnet-4-5-20250929

  workflows:
    - dev-story
    - review-story
```

**File**: `gao_dev/core/agent_config_loader.py`
```python
class AgentConfigLoader:
    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir

    def load_agent(self, agent_name: str) -> AgentConfig:
        """Load agent config from YAML."""
        yaml_path = self.agents_dir / f"{agent_name}.agent.yaml"
        persona_path = self.agents_dir / f"{agent_name}.md"

        # Load YAML
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Load persona
        persona = persona_path.read_text()

        return AgentConfig.from_dict(data["agent"], persona)
```

**File**: `gao_dev/core/factories/agent_factory.py` (refactored)
```python
def _register_builtin_agents(self) -> None:
    """Register all built-in GAO-Dev agents."""
    loader = AgentConfigLoader(self.config.get_agents_path())

    # Discover all .agent.yaml files
    for agent_file in self.config.get_agents_path().glob("*.agent.yaml"):
        agent_name = agent_file.stem  # Remove .agent.yaml
        config = loader.load_agent(agent_name)
        self._agent_configs[agent_name] = config
```

---

## Implementation Plan

### Step 1: Create AgentConfig Data Model
**File**: `gao_dev/core/models/agent_config.py`

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

@dataclass
class AgentConfig:
    """Agent configuration loaded from YAML."""

    name: str
    role: str
    persona: str
    tools: List[str]
    capabilities: List[str]
    model: str
    workflows: List[str]
    icon: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict, persona: str) -> "AgentConfig":
        """Create from parsed YAML dict."""
        return cls(
            name=data["metadata"]["name"],
            role=data["metadata"]["role"],
            persona=persona,
            tools=data["tools"],
            capabilities=data.get("capabilities", []),
            model=data.get("model", "claude-sonnet-4-5-20250929"),
            workflows=data.get("workflows", []),
            icon=data["metadata"].get("icon"),
            version=data["metadata"].get("version", "1.0.0"),
            metadata=data.get("config", {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "role": self.role,
            "tools": self.tools,
            "capabilities": self.capabilities,
            "model": self.model,
            "workflows": self.workflows,
            "icon": self.icon,
            "version": self.version,
        }
```

### Step 2: Create AgentConfigLoader
**File**: `gao_dev/core/agent_config_loader.py`

```python
import yaml
from pathlib import Path
from typing import List
from .models.agent_config import AgentConfig

class AgentConfigLoader:
    """Load agent configurations from YAML files."""

    def __init__(self, agents_dir: Path):
        self.agents_dir = agents_dir

    def load_agent(self, agent_name: str) -> AgentConfig:
        """
        Load agent configuration by name.

        Args:
            agent_name: Agent name (e.g., "amelia")

        Returns:
            AgentConfig with metadata and persona

        Raises:
            FileNotFoundError: If YAML or persona not found
            ValueError: If YAML invalid
        """
        yaml_path = self.agents_dir / f"{agent_name}.agent.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Agent config not found: {yaml_path}")

        # Load YAML
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Load persona
        persona_file = data["agent"].get("persona_file")
        if persona_file:
            persona_path = self.agents_dir / persona_file
            if not persona_path.exists():
                raise FileNotFoundError(f"Persona not found: {persona_path}")
            persona = persona_path.read_text(encoding="utf-8")
        elif "persona" in data["agent"]:
            persona = data["agent"]["persona"]
        else:
            raise ValueError(f"No persona_file or persona in {yaml_path}")

        return AgentConfig.from_dict(data["agent"], persona)

    def discover_agents(self) -> List[str]:
        """
        Discover all agent YAML files.

        Returns:
            List of agent names
        """
        return [
            f.stem  # Remove .agent.yaml extension
            for f in self.agents_dir.glob("*.agent.yaml")
        ]
```

### Step 3: Create YAML Files for All Agents
Create 8 YAML files following this template:

**Template**: `{agent_name}.agent.yaml`
```yaml
agent:
  metadata:
    name: {AgentName}
    role: {Role}
    icon: {Icon}
    version: 1.0.0

  persona_file: ./{agent_name}.md

  tools:
    - {list of tools}

  capabilities:
    - {list of capabilities}

  model: claude-sonnet-4-5-20250929

  workflows:
    - {list of workflows}
```

### Step 4: Refactor AgentFactory
Update `_register_builtin_agents()` to use loader.

### Step 5: Update Tests
- Add tests for AgentConfigLoader
- Update AgentFactory tests
- Add integration tests

---

## Testing Requirements

### Unit Tests

**File**: `tests/core/test_agent_config_loader.py`
```python
def test_load_agent_success():
    """Test loading valid agent YAML."""
    loader = AgentConfigLoader(Path("gao_dev/agents"))
    config = loader.load_agent("amelia")

    assert config.name == "Amelia"
    assert config.role == "Software Developer"
    assert "Read" in config.tools
    assert "Write" in config.tools
    assert config.persona  # Non-empty

def test_load_agent_file_not_found():
    """Test error when agent YAML missing."""
    loader = AgentConfigLoader(Path("gao_dev/agents"))
    with pytest.raises(FileNotFoundError):
        loader.load_agent("nonexistent")

def test_discover_agents():
    """Test agent discovery."""
    loader = AgentConfigLoader(Path("gao_dev/agents"))
    agents = loader.discover_agents()

    assert "amelia" in agents
    assert "bob" in agents
    assert len(agents) == 8
```

### Integration Tests

**File**: `tests/integration/test_agent_factory_yaml.py`
```python
def test_agent_factory_loads_from_yaml():
    """Test AgentFactory loads agents from YAML."""
    factory = AgentFactory(config)
    factory._register_builtin_agents()

    # All 8 agents registered
    assert len(factory._agent_configs) == 8

    # Amelia loaded correctly
    amelia = factory.create_agent("amelia")
    assert amelia is not None
    assert "Read" in amelia.tools
    assert "Write" in amelia.tools

def test_same_functionality_as_before():
    """Verify same behavior as hardcoded approach."""
    # This test ensures zero regressions
    factory = AgentFactory(config)

    # All agents can be created
    for agent_name in ["mary", "john", "winston", "sally", "bob", "amelia", "murat", "brian"]:
        agent = factory.create_agent(agent_name)
        assert agent is not None
```

---

## Dependencies

**None** - This is a foundation story

**Blocks**:
- Story 8.6 (Schema Validation)
- Story 8.7 (Plugin System Enhancement)

---

## Definition of Done

- [ ] All 8 agent YAML files created
- [ ] AgentConfigLoader implemented and tested
- [ ] AgentConfig data model created
- [ ] AgentFactory refactored to use loader
- [ ] All hardcoded agent configs removed
- [ ] Zero duplicate configurations
- [ ] All existing tests passing
- [ ] New tests added (80%+ coverage)
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Atomic git commit with clear message

---

## Notes

**Migration Strategy**:
1. Create loader and data model first
2. Migrate Amelia as proof of concept
3. Verify tests pass for Amelia
4. Migrate remaining 7 agents
5. Remove hardcoded configs
6. Final validation

**Backwards Compatibility**:
- Keep existing AgentFactory interface
- Internal implementation changes only
- No breaking changes to API

**Performance**:
- Lazy loading (load on demand)
- Cache loaded configs
- Target: <50ms per agent load

---

## References

- **BMAD Agent Format**: `bmad/bmm/agents/dev.agent.yaml`
- **Current AgentFactory**: `gao_dev/core/factories/agent_factory.py`
- **Agent Personas**: `gao_dev/agents/*.md`
- **PRD**: `docs/features/prompt-abstraction/PRD.md`
- **Architecture**: `docs/features/prompt-abstraction/ARCHITECTURE.md`
