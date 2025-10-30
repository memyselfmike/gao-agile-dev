# Story 6.6: Extract Services from SandboxManager

**Epic**: 6 - Legacy Cleanup & God Class Refactoring
**Story Points**: 8
**Priority**: P0 (Critical)
**Type**: Refactoring
**Status**: Ready

---

## Overview

Extract three services from the 781-line `SandboxManager`: `ProjectRepository`, `ProjectLifecycle`, and `BenchmarkTracker`.

---

## User Story

**As a** GAO-Dev architect
**I want** sandbox logic decomposed into focused services
**So that** each service has single responsibility and is testable

---

## Acceptance Criteria

1. **ProjectRepository** (< 200 lines)
   - [ ] Created in `gao_dev/sandbox/repositories/project_repository.py`
   - [ ] Handles all project CRUD operations
   - [ ] Manages project metadata persistence
   - [ ] Implements IRepository interface
   - [ ] Separates data access from business logic

2. **ProjectLifecycle** (< 150 lines)
   - [ ] Created in `gao_dev/sandbox/project_lifecycle.py`
   - [ ] Manages project state machine
   - [ ] Validates state transitions
   - [ ] Publishes lifecycle events
   - [ ] States: initialized → building → testing → completed → failed

3. **BenchmarkTracker** (< 100 lines)
   - [ ] Created in `gao_dev/sandbox/benchmark_tracker.py` (or enhance existing)
   - [ ] Tracks benchmark run history
   - [ ] Records metrics per run
   - [ ] Provides run statistics
   - [ ] Persists run data

4. **Testing**
   - [ ] Unit tests for each service (80%+ coverage)
   - [ ] State machine tests for ProjectLifecycle
   - [ ] CRUD tests for ProjectRepository
   - [ ] Tracking tests for BenchmarkTracker

5. **Documentation**
   - [ ] Docstrings for all services
   - [ ] Type hints throughout
   - [ ] State machine diagram for ProjectLifecycle

---

## Technical Details

### ProjectRepository

```python
class ProjectRepository(IRepository[Project]):
    """Repository for sandbox project data access."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path

    async def find_by_id(self, project_id: str) -> Optional[Project]:
        """Find project by ID."""
        pass

    async def find_all(self) -> List[Project]:
        """Find all projects."""
        pass

    async def save(self, project: Project) -> None:
        """Save project metadata."""
        pass

    async def delete(self, project_id: str) -> None:
        """Delete project."""
        pass

    async def exists(self, project_id: str) -> bool:
        """Check if project exists."""
        pass
```

### ProjectLifecycle

```python
class ProjectLifecycle:
    """Manages sandbox project state machine."""

    VALID_TRANSITIONS = {
        ProjectStatus.INITIALIZED: [ProjectStatus.BUILDING],
        ProjectStatus.BUILDING: [ProjectStatus.TESTING, ProjectStatus.FAILED],
        ProjectStatus.TESTING: [ProjectStatus.COMPLETED, ProjectStatus.FAILED],
        ProjectStatus.COMPLETED: [],
        ProjectStatus.FAILED: [ProjectStatus.INITIALIZED]  # Can reset
    }

    def __init__(
        self,
        project_repository: ProjectRepository,
        event_bus: IEventBus
    ):
        pass

    async def transition(
        self,
        project_id: str,
        new_status: ProjectStatus
    ) -> Project:
        """Transition project to new status with validation."""
        pass

    def is_valid_transition(
        self,
        current: ProjectStatus,
        new: ProjectStatus
    ) -> bool:
        """Check if transition is valid."""
        pass
```

### BenchmarkTracker

```python
class BenchmarkTracker:
    """Tracks benchmark run history and metrics."""

    def __init__(self, runs_path: Path):
        self.runs_path = runs_path

    async def record_run(
        self,
        project_id: str,
        run: BenchmarkRun
    ) -> None:
        """Record a benchmark run."""
        pass

    async def get_runs(
        self,
        project_id: str,
        limit: Optional[int] = None
    ) -> List[BenchmarkRun]:
        """Get run history for project."""
        pass

    async def get_statistics(
        self,
        project_id: str
    ) -> BenchmarkStatistics:
        """Get statistics for project runs."""
        pass
```

---

## Implementation Steps

1. **Create ProjectRepository**
   - Extract CRUD logic from SandboxManager
   - Implement IRepository interface
   - Write unit tests

2. **Create ProjectLifecycle**
   - Extract state machine logic
   - Define valid transitions
   - Add event publishing
   - Write state machine tests

3. **Create/Enhance BenchmarkTracker**
   - Extract run tracking logic
   - Add statistics calculation
   - Write tests

4. **Update Imports**
   - Add service imports to SandboxManager
   - Remove extracted code
   - Prepare for Story 6.7 facade refactor

---

## Definition of Done

- [ ] All 3 services created
- [ ] Each service < specified line limit
- [ ] Unit tests for all services (80%+ coverage)
- [ ] Integration tests pass
- [ ] Code reviewed
- [ ] Ready for Story 6.7 (facade refactor)

---

## Dependencies

None - Can start immediately

---

**Related Stories**: 6.7 (SandboxManager Facade)
**Estimated Time**: 1.5-2 days
