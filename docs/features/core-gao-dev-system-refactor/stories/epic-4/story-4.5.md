# Story 4.5: Implement Extension Points (Hooks)

**Epic**: Epic 4 - Plugin Architecture
**Story Points**: 5
**Priority**: P1 (High)
**Status**: Not Started

---

## User Story

**As a** plugin developer
**I want** to hook into GAO-Dev lifecycle events
**So that** my plugins can react to system events and extend core functionality

---

## Description

Create an extension point system that allows plugins to register hooks for lifecycle events. This enables plugins to execute custom code at specific points in the workflow, agent, and system lifecycle without modifying core code.

**Current State**: Plugins can provide agents and workflows but cannot hook into lifecycle events (workflow start/end, agent creation, etc.).

**Target State**: HookManager coordinates hook registration and execution. Plugins can register hooks for lifecycle events and receive event notifications.

---

## Acceptance Criteria

### HookManager Implementation

- [ ] **Class created**: `gao_dev/core/hook_manager.py`
- [ ] **Size**: < 300 lines
- [ ] **Single responsibility**: Manage hook registration and execution

### Core Methods

- [ ] **register_hook(event_type, handler, priority)** -> None
  - Register hook handler for specific event type
  - Support priority ordering (higher priority executes first)
  - Validate handler signature matches event type
  - Prevent duplicate handler registration
  - Log hook registration

- [ ] **unregister_hook(event_type, handler)** -> bool
  - Remove registered hook handler
  - Return true if handler was found and removed
  - Log hook unregistration

- [ ] **execute_hooks(event_type, event_data)** -> HookResults
  - Execute all registered hooks for event type
  - Execute in priority order
  - Pass event_data to each handler
  - Collect results from all handlers
  - Handle handler exceptions gracefully
  - Log hook execution and errors
  - Support async and sync handlers

- [ ] **get_registered_hooks(event_type)** -> List[HookInfo]
  - Return list of registered hooks for event type
  - Include handler, priority, and metadata
  - Support listing all hooks (no event_type filter)

### Hook Event Types

- [ ] **HookEventType enum** created with events:
  - WORKFLOW_START = "workflow.start"
  - WORKFLOW_END = "workflow.end"
  - WORKFLOW_ERROR = "workflow.error"
  - AGENT_CREATED = "agent.created"
  - AGENT_EXECUTE_START = "agent.execute.start"
  - AGENT_EXECUTE_END = "agent.execute.end"
  - PLUGIN_LOADED = "plugin.loaded"
  - PLUGIN_ERROR = "plugin.error"
  - SYSTEM_STARTUP = "system.startup"
  - SYSTEM_SHUTDOWN = "system.shutdown"

### Hook Data Models

- [ ] **HookHandler Protocol** defined:
  - Callable with signature: (event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]
  - Support both sync and async handlers
  - Return value optional (can be used by subsequent hooks)

- [ ] **HookInfo dataclass** created:
  - event_type: HookEventType
  - handler: HookHandler
  - priority: int (default 100, higher = earlier)
  - name: str (for logging)
  - plugin_name: Optional[str]

- [ ] **HookResults dataclass** created:
  - executed_count: int
  - failed_count: int
  - results: List[Any]
  - errors: List[Exception]

### BasePlugin Integration

- [ ] **register_hooks() method** added to BasePlugin:
  - Called during plugin initialization
  - Plugins override to register their hooks
  - Access to HookManager instance
  - Example implementation provided

- [ ] **unregister_hooks() method** added to BasePlugin:
  - Called during plugin cleanup
  - Automatically unregister all plugin hooks
  - Prevent memory leaks

### Hook Execution Points

- [ ] **Workflow lifecycle hooks** integrated:
  - WORKFLOW_START fired before workflow execution
  - WORKFLOW_END fired after successful completion
  - WORKFLOW_ERROR fired on workflow failure
  - Event data includes workflow_id, context, result

- [ ] **Agent lifecycle hooks** integrated:
  - AGENT_CREATED fired when agent instantiated
  - AGENT_EXECUTE_START fired before agent execution
  - AGENT_EXECUTE_END fired after agent execution
  - Event data includes agent_name, input, output

- [ ] **Plugin lifecycle hooks** integrated:
  - PLUGIN_LOADED fired after plugin successfully loaded
  - PLUGIN_ERROR fired on plugin load/execution error
  - Event data includes plugin_name, metadata, error

### Testing

- [ ] Unit tests for HookManager (85%+ coverage)
- [ ] Unit tests for hook registration/unregistration
- [ ] Unit tests for hook execution (sync and async)
- [ ] Unit tests for priority ordering
- [ ] Integration test: Plugin registers and receives hooks
- [ ] Integration test: Multiple hooks for same event
- [ ] All existing tests still pass

---

## Technical Details

### Implementation Strategy

1. **Create HookManager class**:
   ```python
   class HookManager:
       """Manages hook registration and execution.

       Provides extension points for plugins to hook into lifecycle events.
       Supports both synchronous and asynchronous handlers.
       """

       def __init__(self):
           self._hooks: Dict[HookEventType, List[HookInfo]] = {}
           self._lock = threading.Lock()

       def register_hook(
           self,
           event_type: HookEventType,
           handler: HookHandler,
           priority: int = 100,
           name: str = None,
           plugin_name: str = None
       ) -> None:
           """Register hook handler for event type."""
           with self._lock:
               if event_type not in self._hooks:
                   self._hooks[event_type] = []

               hook_info = HookInfo(
                   event_type=event_type,
                   handler=handler,
                   priority=priority,
                   name=name or handler.__name__,
                   plugin_name=plugin_name
               )

               self._hooks[event_type].append(hook_info)
               self._hooks[event_type].sort(key=lambda h: h.priority, reverse=True)

               logger.info(
                   "hook_registered",
                   event_type=event_type.value,
                   handler_name=hook_info.name,
                   priority=priority
               )

       async def execute_hooks(
           self,
           event_type: HookEventType,
           event_data: Dict[str, Any]
       ) -> HookResults:
           """Execute all registered hooks for event type."""
           hooks = self._hooks.get(event_type, [])

           executed_count = 0
           failed_count = 0
           results = []
           errors = []

           for hook_info in hooks:
               try:
                   if asyncio.iscoroutinefunction(hook_info.handler):
                       result = await hook_info.handler(event_data)
                   else:
                       result = hook_info.handler(event_data)

                   results.append(result)
                   executed_count += 1

               except Exception as e:
                   logger.error(
                       "hook_execution_failed",
                       event_type=event_type.value,
                       handler_name=hook_info.name,
                       error=str(e)
                   )
                   errors.append(e)
                   failed_count += 1

           return HookResults(
               executed_count=executed_count,
               failed_count=failed_count,
               results=results,
               errors=errors
           )
   ```

2. **Update BasePlugin with hook support**:
   ```python
   class BasePlugin(ABC):
       """Base class for all plugins."""

       def __init__(self):
           self._hook_manager: Optional[HookManager] = None

       def set_hook_manager(self, hook_manager: HookManager) -> None:
           """Set hook manager instance."""
           self._hook_manager = hook_manager

       def register_hooks(self) -> None:
           """Override to register plugin hooks.

           Example:
               def register_hooks(self):
                   self._hook_manager.register_hook(
                       HookEventType.WORKFLOW_START,
                       self._on_workflow_start,
                       priority=100,
                       plugin_name=self.name
                   )
           """
           pass

       def unregister_hooks(self) -> None:
           """Unregister all plugin hooks."""
           if self._hook_manager:
               # Unregister all hooks registered by this plugin
               for event_type, hooks in self._hook_manager._hooks.items():
                   self._hook_manager._hooks[event_type] = [
                       h for h in hooks if h.plugin_name != self.name
                   ]
   ```

3. **Integrate hooks into workflow execution**:
   ```python
   # In WorkflowExecutor or similar
   async def execute_workflow(self, workflow: IWorkflow, context: WorkflowContext):
       # Fire WORKFLOW_START hook
       await self.hook_manager.execute_hooks(
           HookEventType.WORKFLOW_START,
           {
               "workflow_id": workflow.identifier,
               "context": context
           }
       )

       try:
           result = await workflow.execute(context)

           # Fire WORKFLOW_END hook
           await self.hook_manager.execute_hooks(
               HookEventType.WORKFLOW_END,
               {
                   "workflow_id": workflow.identifier,
                   "context": context,
                   "result": result
               }
           )

           return result

       except Exception as e:
           # Fire WORKFLOW_ERROR hook
           await self.hook_manager.execute_hooks(
               HookEventType.WORKFLOW_ERROR,
               {
                   "workflow_id": workflow.identifier,
                   "context": context,
                   "error": e
               }
           )
           raise
   ```

4. **Create example hook in plugin**:
   ```python
   # In example plugin
   class ExampleWorkflowPlugin(BaseWorkflowPlugin):
       def register_hooks(self):
           """Register hooks for workflow events."""
           if self._hook_manager:
               self._hook_manager.register_hook(
                   HookEventType.WORKFLOW_START,
                   self._log_workflow_start,
                   priority=100,
                   plugin_name="example-workflow-plugin"
               )

       def _log_workflow_start(self, event_data: Dict[str, Any]) -> None:
           """Log workflow start event."""
           workflow_id = event_data.get("workflow_id")
           logger.info(
               "plugin_workflow_start",
               workflow_id=str(workflow_id),
               plugin="example-workflow-plugin"
           )
   ```

---

## Dependencies

- **Depends On**:
  - Story 4.1 complete (PluginDiscovery)
  - Story 4.2 complete (PluginLoader)
  - Story 4.3 complete (BaseAgentPlugin)
  - Story 4.4 complete (BaseWorkflowPlugin)

- **Blocks**:
  - Story 4.6 (Security needs to control hooks)
  - Story 4.7 (Example plugins will use hooks)

---

## Definition of Done

- [ ] HookManager class < 300 lines
- [ ] 10+ hook event types defined
- [ ] BasePlugin supports register_hooks() and unregister_hooks()
- [ ] Hooks integrated into workflow lifecycle
- [ ] Hooks integrated into agent lifecycle
- [ ] Example plugin uses hooks
- [ ] 85%+ test coverage for new code
- [ ] All existing tests pass (100%)
- [ ] Integration test: hook execution works end-to-end
- [ ] Code review approved
- [ ] Merged to feature branch
- [ ] Documentation updated

---

## Files to Create

1. `gao_dev/core/hook_manager.py` (HookManager)
2. `gao_dev/core/models/hook.py` (HookInfo, HookResults, HookEventType)
3. `tests/core/test_hook_manager.py`
4. `tests/plugins/fixtures/hooks_example_plugin/` (example using hooks)

---

## Files to Modify

1. `gao_dev/plugins/base_plugin.py` - Add hook methods
2. `gao_dev/plugins/loader.py` - Call register_hooks() after initialize()
3. `gao_dev/core/workflow_executor.py` - Fire workflow hooks (if exists)
4. `gao_dev/orchestrator/orchestrator.py` - Fire system hooks
5. `gao_dev/core/__init__.py` - Export HookManager
6. `gao_dev/core/models/__init__.py` - Export hook models

---

## Related

- **Epic**: Epic 4 - Plugin Architecture
- **Previous Story**: Story 4.4 - Create Plugin API for Workflows
- **Next Story**: Story 4.6 - Implement Plugin Security and Sandboxing
- **Interfaces**: BasePlugin, HookHandler
- **Dependencies**: HookManager, PluginLoader

---

## Test Plan

### Unit Tests

1. **Test HookManager**:
   - Register hooks for different event types
   - Unregister hooks
   - Execute hooks in priority order
   - Handle handler exceptions
   - Support async and sync handlers

2. **Test BasePlugin hooks**:
   - register_hooks() called during initialization
   - unregister_hooks() called during cleanup
   - Hooks properly registered with HookManager

3. **Test hook execution**:
   - Hooks receive correct event data
   - Results collected from all hooks
   - Errors don't stop other hooks
   - Priority ordering works

### Integration Tests

1. **End-to-end hook workflow**:
   - Create plugin with hooks
   - Load plugin
   - Execute workflow
   - Verify hooks received events
   - Cleanup removes hooks

---

## Security Considerations

- Hooks can modify event data passed to subsequent hooks
- Malicious hooks could cause performance issues (addressed in Story 4.6)
- Hook handlers should be timeout-protected (Story 4.6)
- Hooks cannot cancel workflow execution (by design)
- Hook errors are logged but don't fail the workflow

---

## Notes

- Hooks are fire-and-forget (don't block workflow execution)
- Hook execution order determined by priority (higher = earlier)
- Async hooks are awaited, sync hooks run in executor
- Hook results available for inspection but don't affect workflow
- Story 4.6 will add timeout and permission controls
- Similar to WordPress hooks, Electron lifecycle events, VS Code extensions
