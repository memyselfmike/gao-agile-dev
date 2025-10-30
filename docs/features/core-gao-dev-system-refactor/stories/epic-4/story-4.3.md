# Story 4.3: Create Plugin API for Agents

**Epic**: Epic 4 - Plugin Architecture
**Story Points**: 5
**Priority**: P1 (High)
**Status**: Done

---

## User Story

**As a** plugin developer
**I want** to create custom agent plugins
**So that** I can extend GAO-Dev with domain-specific agents without modifying core code

---

## Description

Create a plugin API that enables developers to create custom agent plugins. Plugin agents should integrate seamlessly with the existing AgentFactory, have access to the same tools and context as built-in agents, and follow the same lifecycle patterns.

**Current State**: Agents are hard-coded in `gao_dev/agents/`. No mechanism exists for adding custom agents via plugins.

**Target State**: Plugin developers can create agent plugins that are discovered, loaded, and registered with AgentFactory automatically.

---

## Acceptance Criteria

### BaseAgentPlugin Class

- [ ] **Class created**: `gao_dev/plugins/agent_plugin.py`
- [ ] **Extends**: `BasePlugin` for lifecycle hooks
- [ ] **Size**: < 200 lines
- [ ] **Single responsibility**: Define agent plugin contract

### Core Methods

- [ ] **get_agent_class()** -> Type[IAgent]
  - Return the agent class to register
  - Must return class that implements IAgent interface
  - Raises PluginError if invalid

- [ ] **get_agent_name()** -> str
  - Return unique agent name
  - Used for registration in AgentFactory
  - Must be unique across all agents

- [ ] **get_agent_metadata()** -> AgentMetadata
  - Return agent metadata (role, description, capabilities)
  - Used for agent discovery and documentation
  - Optional fields handled gracefully

### AgentPluginManager Integration

- [ ] **Class created**: `gao_dev/plugins/agent_plugin_manager.py`
- [ ] **Integrates**: PluginDiscovery, PluginLoader, AgentFactory
- [ ] **Methods**:
  - `discover_agent_plugins()` -> List[PluginMetadata]
  - `load_agent_plugins()` -> Dict[str, str] (results)
  - `register_agent_plugins()` -> int (count registered)
  - `get_available_agents()` -> List[str]

### AgentFactory Integration

- [ ] **Modified**: `gao_dev/core/factories/agent_factory.py`
- [ ] **New method**: `register_plugin_agent(name, agent_class)`
- [ ] **Behavior**: Plugin agents treated same as built-in agents
- [ ] **Validation**: Agent class implements IAgent interface
- [ ] **Error handling**: DuplicateAgentError if name conflict

### AgentMetadata Model

- [ ] **Dataclass created**: `gao_dev/plugins/models.py` (add to existing)
- [ ] **Fields**:
  - name: str
  - role: str
  - description: str
  - capabilities: List[str]
  - tools: List[str]
  - model: str (default: "claude-sonnet-4-5-20250929")

### Example Plugin

- [ ] **Created**: `tests/plugins/fixtures/example_agent_plugin/`
- [ ] **Structure**:
  ```
  example_agent_plugin/
    __init__.py
    plugin.yaml
    agent_plugin.py    # BaseAgentPlugin implementation
    agent.py          # IAgent implementation
  ```
- [ ] **Functionality**: Complete working example
- [ ] **Documentation**: README.md with usage instructions

### Testing

- [ ] Unit tests for BaseAgentPlugin (85%+ coverage)
- [ ] Unit tests for AgentPluginManager (85%+ coverage)
- [ ] Integration test: Discover → Load → Register → Use
- [ ] Test agent plugin with AgentFactory
- [ ] Test plugin agent execution
- [ ] All existing tests still pass

---

## Technical Details

### Implementation Strategy

1. **Create BaseAgentPlugin class**:
   ```python
   from abc import abstractmethod
   from typing import Type
   from .base_plugin import BasePlugin
   from ..core.interfaces.agent import IAgent
   from .models import AgentMetadata

   class BaseAgentPlugin(BasePlugin):
       """Base class for agent plugins.

       Agent plugins provide custom agents that integrate with
       GAO-Dev's agent system. Plugin agents have access to the
       same tools and capabilities as built-in agents.

       Example:
           ```python
           class DomainExpertPlugin(BaseAgentPlugin):
               def get_agent_class(self) -> Type[IAgent]:
                   return DomainExpertAgent

               def get_agent_name(self) -> str:
                   return "DomainExpert"

               def get_agent_metadata(self) -> AgentMetadata:
                   return AgentMetadata(
                       name="DomainExpert",
                       role="Domain Expert",
                       description="Expert in specific domain knowledge",
                       capabilities=["analysis", "consultation"],
                       tools=["Read", "Grep", "WebFetch"]
                   )
           ```
       """

       @abstractmethod
       def get_agent_class(self) -> Type[IAgent]:
           """Get the agent class to register."""
           pass

       @abstractmethod
       def get_agent_name(self) -> str:
           """Get unique agent name."""
           pass

       @abstractmethod
       def get_agent_metadata(self) -> AgentMetadata:
           """Get agent metadata."""
           pass
   ```

2. **Create AgentPluginManager**:
   ```python
   class AgentPluginManager:
       """Manages agent plugins.

       Coordinates plugin discovery, loading, and registration
       with the AgentFactory.
       """

       def __init__(
           self,
           plugin_discovery: PluginDiscovery,
           plugin_loader: PluginLoader,
           agent_factory: AgentFactory
       ):
           self.discovery = plugin_discovery
           self.loader = plugin_loader
           self.factory = agent_factory

       def discover_agent_plugins(self) -> List[PluginMetadata]:
           """Discover all agent plugins."""
           plugin_dirs = self.discovery.get_plugin_dirs()
           all_plugins = self.discovery.discover_plugins(plugin_dirs)
           # Filter for agent type
           return [p for p in all_plugins if p.type == PluginType.AGENT]

       def load_agent_plugins(self) -> Dict[str, str]:
           """Load all agent plugins."""
           agent_plugins = self.discover_agent_plugins()
           return self.loader.load_all_enabled(agent_plugins)

       def register_agent_plugins(self) -> int:
           """Register loaded agent plugins with factory."""
           count = 0
           for plugin_name in self.loader.list_loaded_plugins():
               try:
                   plugin = self.loader.get_loaded_plugin(plugin_name)
                   metadata = self.loader.get_plugin_metadata(plugin_name)

                   # Only process agent plugins
                   if metadata.type != PluginType.AGENT:
                       continue

                   # Verify it's an agent plugin
                   if not isinstance(plugin, BaseAgentPlugin):
                       logger.warning(
                           "agent_plugin_invalid_type",
                           plugin_name=plugin_name
                       )
                       continue

                   # Get agent details
                   agent_class = plugin.get_agent_class()
                   agent_name = plugin.get_agent_name()

                   # Register with factory
                   self.factory.register_plugin_agent(agent_name, agent_class)
                   count += 1

               except Exception as e:
                   logger.error(
                       "agent_plugin_registration_failed",
                       plugin_name=plugin_name,
                       error=str(e)
                   )

           return count

       def get_available_agents(self) -> List[str]:
           """Get list of all available agents (built-in + plugins)."""
           return self.factory.list_agents()
   ```

3. **Update AgentFactory**:
   ```python
   # Add to existing AgentFactory class

   def register_plugin_agent(
       self,
       name: str,
       agent_class: Type[IAgent]
   ) -> None:
       """Register a plugin agent.

       Args:
           name: Unique agent name
           agent_class: Agent class implementing IAgent

       Raises:
           DuplicateAgentError: If agent name already registered
           InvalidAgentError: If agent_class doesn't implement IAgent
       """
       # Validate implements IAgent
       if not issubclass(agent_class, IAgent):
           raise InvalidAgentError(
               f"Agent class must implement IAgent interface"
           )

       # Check for duplicates
       if name.lower() in self._agent_classes:
           raise DuplicateAgentError(
               f"Agent '{name}' is already registered"
           )

       # Register
       self._agent_classes[name.lower()] = agent_class

       logger.info(
           "plugin_agent_registered",
           agent_name=name,
           agent_class=agent_class.__name__
       )
   ```

4. **Create AgentMetadata model**:
   ```python
   @dataclass
   class AgentMetadata:
       """Metadata for an agent plugin."""
       name: str
       role: str
       description: str
       capabilities: List[str] = field(default_factory=list)
       tools: List[str] = field(default_factory=list)
       model: str = "claude-sonnet-4-5-20250929"
   ```

---

## Dependencies

- **Depends On**:
  - Story 4.1 complete (PluginDiscovery)
  - Story 4.2 complete (PluginLoader, BasePlugin)
  - Epic 3 complete (AgentFactory)

- **Blocks**:
  - Story 4.5 (Extension points need agent plugins)
  - Story 4.7 (Example plugins)

---

## Definition of Done

- [ ] BaseAgentPlugin class < 200 lines
- [ ] AgentPluginManager class < 250 lines
- [ ] AgentFactory updated with register_plugin_agent()
- [ ] AgentMetadata model created
- [ ] Example agent plugin works end-to-end
- [ ] 85%+ test coverage for new code
- [ ] All existing tests pass (100%)
- [ ] Integration test: discover → load → register → use
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/plugins/agent_plugin.py` (BaseAgentPlugin)
2. `gao_dev/plugins/agent_plugin_manager.py` (AgentPluginManager)
3. `tests/plugins/test_agent_plugin.py`
4. `tests/plugins/fixtures/example_agent_plugin/` (complete example)
5. `tests/plugins/fixtures/example_agent_plugin/plugin.yaml`
6. `tests/plugins/fixtures/example_agent_plugin/agent_plugin.py`
7. `tests/plugins/fixtures/example_agent_plugin/agent.py`
8. `tests/plugins/fixtures/example_agent_plugin/README.md`

---

## Files to Modify

1. `gao_dev/plugins/__init__.py` - Export BaseAgentPlugin, AgentPluginManager
2. `gao_dev/plugins/models.py` - Add AgentMetadata
3. `gao_dev/core/factories/agent_factory.py` - Add register_plugin_agent()
4. `gao_dev/agents/exceptions.py` - Add InvalidAgentError

---

## Related

- **Epic**: Epic 4 - Plugin Architecture
- **Previous Story**: Story 4.2 - Plugin Loading and Lifecycle
- **Next Story**: Story 4.4 - Create Plugin API for Workflows
- **Interfaces**: IAgent, BasePlugin
- **Dependencies**: AgentFactory, PluginDiscovery, PluginLoader

---

## Test Plan

### Unit Tests

1. **Test BaseAgentPlugin**:
   - Abstract methods enforced
   - Can subclass and implement
   - Returns correct agent class
   - Returns correct metadata

2. **Test AgentPluginManager**:
   - Discovers agent plugins only
   - Loads agent plugins
   - Registers with AgentFactory
   - Handles errors gracefully

3. **Test AgentFactory registration**:
   - register_plugin_agent() validates IAgent
   - Rejects duplicate agent names
   - Rejects invalid agent classes
   - Plugin agents accessible via create_agent()

### Integration Tests

1. **End-to-end flow**:
   - Create example agent plugin
   - Discover via AgentPluginManager
   - Load plugin
   - Register with AgentFactory
   - Create agent instance
   - Execute agent task
   - Verify output

---

## Security Considerations

- Validate all agent plugins implement IAgent interface
- Prevent duplicate agent registration (name conflicts)
- Agent plugins sandboxed via Story 4.6 (future)
- Log all agent plugin operations for audit trail

---

## Notes

- Plugin agents have same capabilities as built-in agents
- Plugin agents can use all available tools
- Plugin agents follow same lifecycle as built-in agents
- Example plugin serves as template for developers
- Story 4.6 will add security sandboxing
