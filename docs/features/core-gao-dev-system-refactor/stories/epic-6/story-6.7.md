# Story 6.7: Refactor SandboxManager as Thin Facade

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 3
**Priority**: P0 (Critical)
**Type**: Refactoring
**Status**: Blocked (Requires 6.6)

---

## Overview

Refactor the 781-line `SandboxManager` into a thin facade (< 150 lines) that delegates to the three extracted services.

---

## User Story

**As a** GAO-Dev architect
**I want** SandboxManager to be a simple coordination facade
**So that** it's maintainable and follows single responsibility

---

## Acceptance Criteria

1. **Size Reduction**
   - [ ] SandboxManager reduced from 781 to < 150 lines
   - [ ] No business logic (only delegation)
   - [ ] Clean public API

2. **Delegation**
   - [ ] Uses `ProjectRepository` for CRUD
   - [ ] Uses `ProjectLifecycle` for state management
   - [ ] Uses `BenchmarkTracker` for run tracking
   - [ ] Other components (GitCloner, etc.) remain as-is

3. **Dependency Injection**
   - [ ] All services injected via constructor
   - [ ] Factory method for default configuration

4. **Backward Compatibility**
   - [ ] Public API unchanged
   - [ ] All CLI commands work
   - [ ] Integration tests pass

---

## Technical Details

### Refactored Structure

```python
class SandboxManager:
    """
    Facade for sandbox project management.

    Delegates to specialized services.
    """

    def __init__(
        self,
        project_repository: ProjectRepository,
        project_lifecycle: ProjectLifecycle,
        benchmark_tracker: BenchmarkTracker,
        git_cloner: GitCloner,
        template_scanner: TemplateScanner,
        # ... other components
    ):
        """Initialize with injected services."""
        self.projects = project_repository
        self.lifecycle = project_lifecycle
        self.benchmarks = benchmark_tracker
        self.git = git_cloner
        self.templates = template_scanner
        # ...

    async def init_project(
        self,
        project_id: str,
        **kwargs
    ) -> Project:
        """Initialize new sandbox project."""
        # Create project via repository
        # Set initial state via lifecycle
        # Delegate to other components
        pass

    async def run_benchmark(
        self,
        benchmark_config: str
    ) -> BenchmarkResult:
        """Run benchmark configuration."""
        # Thin coordination logic
        pass

    async def get_project_status(
        self,
        project_id: str
    ) -> ProjectStatus:
        """Get project status."""
        # Simple delegation
        return await self.lifecycle.get_status(project_id)
```

---

## Implementation Steps

1. Add service parameters to constructor
2. Replace inline logic with service calls
3. Remove extracted code
4. Simplify methods (< 20 lines each)
5. Update tests
6. Verify backward compatibility

---

## Definition of Done

- [ ] SandboxManager < 150 lines
- [ ] All business logic in services
- [ ] Dependency injection complete
- [ ] All CLI commands work
- [ ] All tests pass
- [ ] Code reviewed

---

## Dependencies

**Requires**: Story 6.6 (Service Extractions)

---

**Related Stories**: 6.6 (Service Extractions)
**Estimated Time**: Half day
**Critical**: Second God Class eliminated!
