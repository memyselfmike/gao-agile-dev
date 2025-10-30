# Story 4.4: Create Plugin API for Workflows

**Epic**: Epic 4 - Plugin Architecture
**Story Points**: 5
**Priority**: P1 (High)
**Status**: Done

---

## User Story

**As a** plugin developer
**I want** to create custom workflow plugins
**So that** I can extend GAO-Dev with domain-specific workflows without modifying core code

---

## Description

Create a plugin API that enables developers to create custom workflow plugins. Plugin workflows should integrate seamlessly with the existing WorkflowRegistry, have access to the same context and tools as built-in workflows, and follow the same lifecycle patterns.

**Current State**: Workflows are hard-coded in `gao_dev/workflows/` and `bmad/bmm/workflows/`. No mechanism exists for adding custom workflows via plugins.

**Target State**: Plugin developers can create workflow plugins that are discovered, loaded, and registered with WorkflowRegistry automatically.

---

## Acceptance Criteria

### BaseWorkflowPlugin Class

- [ ] **Class created**: `gao_dev/plugins/workflow_plugin.py`
- [ ] **Extends**: `BasePlugin` for lifecycle hooks
- [ ] **Size**: < 200 lines
- [ ] **Single responsibility**: Define workflow plugin contract

### Core Methods

- [ ] **get_workflow_class()** -> Type[IWorkflow]
  - Return the workflow class to register
  - Must return class that implements IWorkflow interface
  - Raises PluginError if invalid

- [ ] **get_workflow_identifier()** -> WorkflowIdentifier
  - Return unique workflow identifier
  - Used for registration in WorkflowRegistry
  - Must be unique across all workflows

- [ ] **get_workflow_metadata()** -> WorkflowMetadata
  - Return workflow metadata (description, phase, tags)
  - Used for workflow discovery and documentation
  - Optional fields handled gracefully

### WorkflowPluginManager Integration

- [ ] **Class created**: `gao_dev/plugins/workflow_plugin_manager.py`
- [ ] **Integrates**: PluginDiscovery, PluginLoader, WorkflowRegistry
- [ ] **Methods**:
  - `discover_workflow_plugins()` -> List[PluginMetadata]
  - `load_workflow_plugins()` -> Dict[str, str] (results)
  - `register_workflow_plugins()` -> int (count registered)
  - `get_available_workflows()` -> List[WorkflowIdentifier]

### WorkflowRegistry Integration

- [ ] **Check if exists**: `gao_dev/core/workflow_registry.py`
- [ ] **New method**: `register_plugin_workflow(identifier, workflow_class)`
- [ ] **Behavior**: Plugin workflows treated same as built-in workflows
- [ ] **Validation**: Workflow class implements IWorkflow interface
- [ ] **Error handling**: DuplicateWorkflowError if identifier conflict

### WorkflowMetadata Model

- [ ] **Dataclass created**: `gao_dev/plugins/models.py` (add to existing)
- [ ] **Fields**:
  - identifier: WorkflowIdentifier
  - description: str
  - phase: int (BMAD phase 1-4)
  - tags: List[str]
  - required_tools: List[str]

### Example Plugin

- [ ] **Created**: `tests/plugins/fixtures/example_workflow_plugin/`
- [ ] **Structure**:
  ```
  example_workflow_plugin/
    __init__.py
    plugin.yaml
    workflow_plugin.py  # BaseWorkflowPlugin implementation
    workflow.py         # IWorkflow implementation
  ```
- [ ] **Functionality**: Complete working example
- [ ] **Documentation**: README.md with usage instructions

### Testing

- [ ] Unit tests for BaseWorkflowPlugin (85%+ coverage)
- [ ] Unit tests for WorkflowPluginManager (85%+ coverage)
- [ ] Integration test: Discover → Load → Register → Execute
- [ ] Test workflow plugin with WorkflowRegistry
- [ ] Test plugin workflow execution
- [ ] All existing tests still pass

---

## Technical Details

### Implementation Strategy

1. **Create BaseWorkflowPlugin class** (similar to BaseAgentPlugin):
   ```python
   from abc import abstractmethod
   from typing import Type
   from .base_plugin import BasePlugin
   from .models import WorkflowMetadata
   from ..core.interfaces.workflow import IWorkflow
   from ..core.models.workflow import WorkflowIdentifier

   class BaseWorkflowPlugin(BasePlugin):
       """Base class for workflow plugins.

       Workflow plugins provide custom workflows that integrate with
       GAO-Dev's workflow system. Plugin workflows have access to the
       same context and tools as built-in workflows.

       Example:
           ```python
           class DomainAnalysisWorkflowPlugin(BaseWorkflowPlugin):
               def get_workflow_class(self):
                   return DomainAnalysisWorkflow

               def get_workflow_identifier(self):
                   return WorkflowIdentifier("domain-analysis", phase=1)

               def get_workflow_metadata(self):
                   return WorkflowMetadata(
                       identifier=self.get_workflow_identifier(),
                       description="Analyze domain-specific requirements",
                       phase=1,
                       tags=["analysis", "domain"],
                       required_tools=["Read", "Grep", "WebFetch"]
                   )
           ```
       """

       @abstractmethod
       def get_workflow_class(self) -> Type[IWorkflow]:
           """Get the workflow class to register."""
           pass

       @abstractmethod
       def get_workflow_identifier(self) -> WorkflowIdentifier:
           """Get unique workflow identifier."""
           pass

       @abstractmethod
       def get_workflow_metadata(self) -> WorkflowMetadata:
           """Get workflow metadata."""
           pass

       def validate_workflow_class(self) -> None:
           """Validate that workflow class implements IWorkflow interface."""
           workflow_class = self.get_workflow_class()

           if not isinstance(workflow_class, type):
               raise PluginError(
                   f"get_workflow_class() must return a class, got {type(workflow_class)}"
               )

           if not issubclass(workflow_class, IWorkflow):
               raise PluginError(
                   f"Workflow class must implement IWorkflow interface"
               )
   ```

2. **Create WorkflowPluginManager** (similar to AgentPluginManager):
   ```python
   class WorkflowPluginManager:
       """Manages workflow plugins."""

       def __init__(
           self,
           plugin_discovery: PluginDiscovery,
           plugin_loader: PluginLoader,
           workflow_registry: WorkflowRegistry
       ):
           self.discovery = plugin_discovery
           self.loader = plugin_loader
           self.registry = workflow_registry

       def discover_workflow_plugins(self) -> List[PluginMetadata]:
           """Discover all workflow plugins."""
           plugin_dirs = self.discovery.get_plugin_dirs()
           all_plugins = self.discovery.discover_plugins(plugin_dirs)
           return [p for p in all_plugins if p.type == PluginType.WORKFLOW]

       def load_workflow_plugins(self) -> Dict[str, str]:
           """Load all workflow plugins."""
           workflow_plugins = self.discover_workflow_plugins()
           return self.loader.load_all_enabled(workflow_plugins)

       def register_workflow_plugins(self) -> int:
           """Register loaded workflow plugins with registry."""
           count = 0
           for plugin_name in self.loader.list_loaded_plugins():
               try:
                   plugin = self.loader.get_loaded_plugin(plugin_name)
                   metadata = self.loader.get_plugin_metadata(plugin_name)

                   if metadata.type != PluginType.WORKFLOW:
                       continue

                   if not isinstance(plugin, BaseWorkflowPlugin):
                       logger.warning("workflow_plugin_invalid_type")
                       continue

                   plugin.validate_workflow_class()

                   workflow_class = plugin.get_workflow_class()
                   identifier = plugin.get_workflow_identifier()

                   self.registry.register_plugin_workflow(identifier, workflow_class)
                   count += 1

               except Exception as e:
                   logger.error("workflow_plugin_registration_failed", error=str(e))

           return count
   ```

3. **Update WorkflowRegistry**:
   ```python
   # Add to existing WorkflowRegistry class

   def register_plugin_workflow(
       self,
       identifier: WorkflowIdentifier,
       workflow_class: Type[IWorkflow]
   ) -> None:
       """Register a plugin workflow."""
       # Validate implements IWorkflow
       if not issubclass(workflow_class, IWorkflow):
           raise RegistrationError(
               f"Workflow class must implement IWorkflow interface"
           )

       # Check for duplicates
       if self.workflow_exists(identifier):
           raise DuplicateWorkflowError(
               f"Workflow '{identifier}' is already registered"
           )

       # Register
       self._workflows[identifier.to_key()] = workflow_class

       logger.info(
           "plugin_workflow_registered",
           identifier=str(identifier),
           workflow_class=workflow_class.__name__
       )
   ```

4. **Create WorkflowMetadata model**:
   ```python
   @dataclass
   class WorkflowMetadata:
       """Metadata for a workflow plugin."""
       identifier: WorkflowIdentifier
       description: str
       phase: int  # BMAD phase 1-4
       tags: List[str] = field(default_factory=list)
       required_tools: List[str] = field(default_factory=list)
   ```

---

## Dependencies

- **Depends On**:
  - Story 4.1 complete (PluginDiscovery)
  - Story 4.2 complete (PluginLoader, BasePlugin)
  - Epic 3 complete (WorkflowRegistry)

- **Blocks**:
  - Story 4.5 (Extension points need workflow plugins)
  - Story 4.7 (Example plugins)

---

## Definition of Done

- [ ] BaseWorkflowPlugin class < 200 lines
- [ ] WorkflowPluginManager class < 250 lines
- [ ] WorkflowRegistry updated with register_plugin_workflow()
- [ ] WorkflowMetadata model created
- [ ] Example workflow plugin works end-to-end
- [ ] 85%+ test coverage for new code
- [ ] All existing tests pass (100%)
- [ ] Integration test: discover → load → register → execute
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/plugins/workflow_plugin.py` (BaseWorkflowPlugin)
2. `gao_dev/plugins/workflow_plugin_manager.py` (WorkflowPluginManager)
3. `tests/plugins/test_workflow_plugin.py`
4. `tests/plugins/fixtures/example_workflow_plugin/` (complete example)
5. `tests/plugins/fixtures/example_workflow_plugin/plugin.yaml`
6. `tests/plugins/fixtures/example_workflow_plugin/workflow_plugin.py`
7. `tests/plugins/fixtures/example_workflow_plugin/workflow.py`
8. `tests/plugins/fixtures/example_workflow_plugin/README.md`

---

## Files to Modify

1. `gao_dev/plugins/__init__.py` - Export BaseWorkflowPlugin, WorkflowPluginManager
2. `gao_dev/plugins/models.py` - Add WorkflowMetadata
3. `gao_dev/core/workflow_registry.py` - Add register_plugin_workflow()

---

## Related

- **Epic**: Epic 4 - Plugin Architecture
- **Previous Story**: Story 4.3 - Create Plugin API for Agents
- **Next Story**: Story 4.5 - Implement Extension Points (Hooks)
- **Interfaces**: IWorkflow, BasePlugin
- **Dependencies**: WorkflowRegistry, PluginDiscovery, PluginLoader

---

## Test Plan

### Unit Tests

1. **Test BaseWorkflowPlugin**:
   - Abstract methods enforced
   - Can subclass and implement
   - Returns correct workflow class
   - Returns correct metadata

2. **Test WorkflowPluginManager**:
   - Discovers workflow plugins only
   - Loads workflow plugins
   - Registers with WorkflowRegistry
   - Handles errors gracefully

3. **Test WorkflowRegistry registration**:
   - register_plugin_workflow() validates IWorkflow
   - Rejects duplicate identifiers
   - Rejects invalid workflow classes
   - Plugin workflows accessible via get_workflow()

### Integration Tests

1. **End-to-end flow**:
   - Create example workflow plugin
   - Discover via WorkflowPluginManager
   - Load plugin
   - Register with WorkflowRegistry
   - Get workflow instance
   - Execute workflow
   - Verify result

---

## Security Considerations

- Validate all workflow plugins implement IWorkflow interface
- Prevent duplicate workflow registration (identifier conflicts)
- Workflow plugins sandboxed via Story 4.6 (future)
- Log all workflow plugin operations for audit trail

---

## Notes

- Plugin workflows have same capabilities as built-in workflows
- Plugin workflows can use all available tools
- Plugin workflows follow same execution patterns
- Example plugin serves as template for developers
- Story 4.6 will add security sandboxing
- Follow same pattern as Story 4.3 (Agent plugins)
