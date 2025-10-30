# Story 6.5: Refactor GAODevOrchestrator as Thin Facade

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 5
**Priority**: P0 (Critical)
**Type**: Refactoring
**Status**: Blocked (Requires 6.1-6.4)

---

## Overview

Refactor the 1,327-line `GAODevOrchestrator` into a thin facade (< 200 lines) that delegates to extracted services.

---

## User Story

**As a** GAO-Dev architect
**I want** the orchestrator to be a simple coordination facade
**So that** it's maintainable, testable, and follows single responsibility

---

## Acceptance Criteria

1. **Size Reduction**
   - [ ] Orchestrator reduced from 1,327 to < 200 lines
   - [ ] No business logic in orchestrator (only delegation)
   - [ ] Clean public API

2. **Delegation**
   - [ ] Uses `WorkflowCoordinator` for workflow execution
   - [ ] Uses `StoryLifecycleManager` for story management
   - [ ] Uses `ProcessExecutor` for subprocess calls
   - [ ] Uses `QualityGateManager` for validation
   - [ ] Uses `BrianOrchestrator` for analysis

3. **Dependency Injection**
   - [ ] All services injected via constructor
   - [ ] Factory method for default configuration
   - [ ] Supports custom service implementations

4. **Backward Compatibility**
   - [ ] Public API unchanged
   - [ ] All existing callers work without modification
   - [ ] Integration tests pass

5. **Testing**
   - [ ] Unit tests with mocked services
   - [ ] Integration tests with real services
   - [ ] All regression tests pass

---

## Technical Details

### Refactored Structure

```python
class GAODevOrchestrator:
    """
    Main orchestrator facade for GAO-Dev.

    Delegates to specialized services for actual work.
    """

    def __init__(
        self,
        workflow_coordinator: WorkflowCoordinator,
        story_lifecycle: StoryLifecycleManager,
        process_executor: ProcessExecutor,
        quality_gate: QualityGateManager,
        brian_orchestrator: BrianOrchestrator,
        methodology_registry: MethodologyRegistry
    ):
        """Initialize with injected services."""
        self.workflow_coordinator = workflow_coordinator
        self.story_lifecycle = story_lifecycle
        self.process_executor = process_executor
        self.quality_gate = quality_gate
        self.brian = brian_orchestrator
        self.methodologies = methodology_registry

    @classmethod
    def create_default(
        cls,
        project_root: Path,
        api_key: Optional[str] = None,
        mode: str = "cli"
    ) -> "GAODevOrchestrator":
        """Factory method for default configuration."""
        # Create all services with standard dependencies
        # Return configured orchestrator
        pass

    async def build_project(self, prompt: str) -> ProjectResult:
        """
        Build complete project from prompt.

        High-level method that delegates to services:
        1. Brian analyzes prompt → complexity assessment
        2. Methodology builds workflow sequence
        3. WorkflowCoordinator executes sequence
        4. QualityGate validates outputs
        5. Return result
        """
        # Thin delegation logic only
        pass

    async def create_and_implement_story(
        self,
        epic: int,
        story: int
    ) -> StoryResult:
        """Create and implement a user story."""
        # Delegate to StoryLifecycleManager and WorkflowCoordinator
        pass
```

---

## Implementation Steps

1. **Create Service Instances**
   - Add all services as constructor parameters
   - Create factory method for default config

2. **Replace Inline Logic**
   - Find all business logic in methods
   - Replace with service method calls
   - Keep only coordination logic

3. **Simplify Methods**
   - Each method should be < 20 lines
   - Clear delegation to services
   - Minimal coordination logic

4. **Remove Duplicates**
   - Delete extracted code (now in services)
   - Remove helper methods (moved to services)
   - Clean up imports

5. **Update Tests**
   - Update tests to mock services
   - Add integration tests
   - Verify backward compatibility

---

## Before/After Comparison

### Before (1,327 lines)
- Workflow execution logic
- Story lifecycle logic
- Subprocess execution
- Quality validation
- Brian integration
- All helper methods
- Configuration loading
- Error handling

### After (< 200 lines)
- Constructor with DI
- Factory method
- 5-6 public API methods
- Simple delegation to services
- Minimal coordination logic
- Clean, readable code

---

## Definition of Done

- [ ] Orchestrator < 200 lines
- [ ] All business logic moved to services
- [ ] Dependency injection complete
- [ ] Factory method created
- [ ] All acceptance criteria met
- [ ] All tests pass (unit + integration)
- [ ] Backward compatibility verified
- [ ] Code reviewed

---

## Dependencies

**Requires Complete**:
- Story 6.1: WorkflowCoordinator
- Story 6.2: StoryLifecycleManager
- Story 6.3: ProcessExecutor
- Story 6.4: QualityGateManager

---

**Related Stories**: 6.1-6.4 (service extractions)
**Estimated Time**: 1 day
**Critical**: This is where we achieve the "no class > 300 lines" goal!
