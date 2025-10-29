# Story 3.1: Implement Factory Pattern for Agents

**Epic**: Epic 3 - Design Pattern Implementation
**Story Points**: 5
**Priority**: P1 (High)
**Status**: Draft

---

## User Story

**As a** core developer
**I want** a centralized factory for creating agent instances
**So that** agent creation is consistent, testable, and extensible without modifying core code

---

## Description

Implement the Factory Pattern for agent creation by creating a concrete `AgentFactory` class that implements the `IAgentFactory` interface. This factory will centralize all agent instantiation logic, replacing hard-coded agent creation throughout the system.

**Current State**: Agents are created via hard-coded `AgentDefinition` objects in `agent_definitions.py` with no centralized creation mechanism.

**Target State**: New `AgentFactory` class in `gao_dev/core/factories/agent_factory.py` that handles all agent creation through a registry pattern.

---

## Acceptance Criteria

### AgentFactory Implementation

- [ ] **Class created**: `gao_dev/core/factories/agent_factory.py`
- [ ] **Implements**: `IAgentFactory` interface completely
- [ ] **Size**: < 200 lines
- [ ] **Single responsibility**: Create and manage agent instances

### Core Methods

- [ ] **create_agent(agent_type, config)** -> IAgent
  - Look up agent class in registry
  - Instantiate with proper configuration
  - Return configured agent instance
  - Raise `AgentNotFoundError` if type not registered
  - Raise `AgentCreationError` if instantiation fails

- [ ] **register_agent_class(agent_type, agent_class)** -> None
  - Validate agent_class implements IAgent
  - Store in internal registry
  - Raise `RegistrationError` if invalid class
  - Raise `DuplicateRegistrationError` if type exists

- [ ] **list_available_agents()** -> List[str]
  - Return all registered agent type identifiers
  - Sorted alphabetically

- [ ] **agent_exists(agent_type)** -> bool
  - Check if agent type registered
  - Case-insensitive lookup

### Built-in Agent Registration

- [ ] **All 8 agents registered** at factory initialization:
  - mary (Business Analyst)
  - john (Product Manager)
  - winston (Technical Architect)
  - sally (UX Designer)
  - bob (Scrum Master)
  - amelia (Software Developer)
  - murat (Test Architect)
  - brian (Workflow Coordinator)

### Integration

- [ ] **Orchestrator refactored**:
  - Uses AgentFactory for all agent creation
  - No direct agent class instantiation
  - Factory injected via constructor

- [ ] **Agent configuration**:
  - AgentConfig model created (if not exists)
  - Supports persona_file, tools, model configuration
  - Type-safe with validation

### Testing

- [ ] Unit tests for AgentFactory (90%+ coverage)
- [ ] Test agent registration and creation
- [ ] Test error handling (not found, duplicate, invalid)
- [ ] Integration tests with orchestrator
- [ ] All existing tests still pass

---

## Technical Details

### Implementation Strategy

1. **Create AgentFactory class**:
   ```python
   class AgentFactory(IAgentFactory):
       """
       Concrete factory for creating agent instances.

       Uses registry pattern to manage agent types. Supports both
       built-in agents and plugin agents.
       """

       def __init__(self, agents_dir: Path):
           """Initialize with path to agent personas."""
           self._registry: Dict[str, Type[IAgent]] = {}
           self._agents_dir = agents_dir
           self._register_builtin_agents()

       def create_agent(
           self,
           agent_type: str,
           config: Optional[AgentConfig] = None
       ) -> IAgent:
           """Create agent instance from registry."""
           agent_type_lower = agent_type.lower()

           if agent_type_lower not in self._registry:
               raise AgentNotFoundError(
                   f"Agent type '{agent_type}' not registered. "
                   f"Available: {self.list_available_agents()}"
               )

           agent_class = self._registry[agent_type_lower]

           try:
               # Load persona if needed
               persona_file = self._agents_dir / f"{agent_type_lower}.md"

               # Create agent instance
               agent = agent_class(
                   name=agent_type.capitalize(),
                   role=config.role if config else "",
                   persona="" if persona_file.exists() else "",
                   tools=config.tools if config else [],
                   model=config.model if config else "claude-sonnet-4-5-20250929",
                   persona_file=persona_file if persona_file.exists() else None
               )

               return agent

           except Exception as e:
               raise AgentCreationError(
                   f"Failed to create agent '{agent_type}': {e}"
               ) from e

       def register_agent_class(
           self,
           agent_type: str,
           agent_class: Type[IAgent]
       ) -> None:
           """Register agent class in factory."""
           # Validate implements IAgent
           if not issubclass(agent_class, IAgent):
               raise RegistrationError(
                   f"Agent class must implement IAgent interface"
               )

           agent_type_lower = agent_type.lower()

           # Check for duplicates
           if agent_type_lower in self._registry:
               raise DuplicateRegistrationError(
                   f"Agent type '{agent_type}' already registered"
               )

           # Register
           self._registry[agent_type_lower] = agent_class

       def _register_builtin_agents(self) -> None:
           """Register all built-in agents."""
           # Import concrete agent classes
           from ...agents.mary import MaryAgent
           from ...agents.john import JohnAgent
           from ...agents.winston import WinstonAgent
           from ...agents.sally import SallyAgent
           from ...agents.bob import BobAgent
           from ...agents.amelia import AmeliaAgent
           from ...agents.murat import MuratAgent
           from ...agents.brian import BrianAgent

           # Register each agent
           self.register_agent_class("mary", MaryAgent)
           self.register_agent_class("john", JohnAgent)
           self.register_agent_class("winston", WinstonAgent)
           self.register_agent_class("sally", SallyAgent)
           self.register_agent_class("bob", BobAgent)
           self.register_agent_class("amelia", AmeliaAgent)
           self.register_agent_class("murat", MuratAgent)
           self.register_agent_class("brian", BrianAgent)
   ```

2. **Create concrete agent classes**:
   - Each agent (Mary, John, etc.) gets its own file
   - Inherits from `PlanningAgent` or `ImplementationAgent`
   - Implements `execute_task()` method

3. **Create AgentConfig model**:
   ```python
   @dataclass
   class AgentConfig:
       """Configuration for agent creation."""
       role: str
       tools: List[str]
       model: str = "claude-sonnet-4-5-20250929"
       persona_file: Optional[Path] = None
   ```

4. **Update orchestrator**:
   ```python
   class GAODevOrchestrator:
       def __init__(
           self,
           # ... other params
           agent_factory: Optional[IAgentFactory] = None
       ):
           # Default factory if not provided
           if agent_factory is None:
               agents_dir = Path(__file__).parent.parent / "agents"
               agent_factory = AgentFactory(agents_dir)

           self.agent_factory = agent_factory

       def _get_agent(self, agent_type: str) -> IAgent:
           """Get agent from factory (replaces hard-coded logic)."""
           config = self._get_agent_config(agent_type)
           return self.agent_factory.create_agent(agent_type, config)
   ```

---

## Dependencies

- **Depends On**:
  - Epic 1 complete (IAgentFactory interface defined)
  - Epic 2 complete (orchestrator refactored)

- **Blocks**:
  - Story 3.2 (Strategy pattern needs factory)
  - Story 4.3 (Plugin agents need factory)

---

## Definition of Done

- [ ] AgentFactory class < 200 lines
- [ ] All 8 built-in agents registered
- [ ] Factory pattern correctly implements IAgentFactory
- [ ] 90%+ test coverage for factory
- [ ] All existing tests pass (100%)
- [ ] Integration test creates all agents via factory
- [ ] Orchestrator uses factory (no hard-coded creation)
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/core/factories/__init__.py`
2. `gao_dev/core/factories/agent_factory.py`
3. `gao_dev/core/models/agent.py` (AgentConfig if not exists)
4. `gao_dev/agents/mary.py` (concrete MaryAgent)
5. `gao_dev/agents/john.py` (concrete JohnAgent)
6. `gao_dev/agents/winston.py` (concrete WinstonAgent)
7. `gao_dev/agents/sally.py` (concrete SallyAgent)
8. `gao_dev/agents/bob.py` (concrete BobAgent)
9. `gao_dev/agents/amelia.py` (concrete AmeliaAgent)
10. `gao_dev/agents/murat.py` (concrete MuratAgent)
11. `gao_dev/agents/brian.py` (concrete BrianAgent)
12. `tests/core/factories/test_agent_factory.py`
13. `tests/integration/test_agent_factory_integration.py`

---

## Files to Modify

1. `gao_dev/orchestrator/orchestrator.py` - Use factory instead of hard-coded creation
2. `gao_dev/orchestrator/agent_definitions.py` - Can be deprecated/removed after migration

---

## Related

- **Epic**: Epic 3 - Design Pattern Implementation
- **Next Story**: Story 3.2 - Implement Strategy Pattern for Workflows
- **Interface**: `gao_dev/core/interfaces/agent.py` (IAgentFactory)
- **Base Classes**: `gao_dev/agents/base.py`
