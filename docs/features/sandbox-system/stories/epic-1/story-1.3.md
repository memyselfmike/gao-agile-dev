# Story 1.3: Project State Management

**Epic**: Epic 1 - Sandbox Infrastructure
**Status**: Draft
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-10-27
**Depends On**: Story 1.2

---

## User Story

**As a** developer using GAO-Dev
**I want** to track and manage sandbox project state
**So that** I can understand project status and history

---

## Acceptance Criteria

### AC1: State Transitions
- ✅ Can transition project between states (active → completed/failed)
- ✅ State transitions are validated (no invalid transitions)
- ✅ State history is tracked
- ✅ Timestamps recorded for each transition

### AC2: Project Status Queries
- ✅ Can get current project status
- ✅ Can filter projects by status
- ✅ Can get status history
- ✅ Can check if project is in specific state

### AC3: Benchmark Run Tracking
- ✅ Can add benchmark run to project
- ✅ Can list all runs for a project
- ✅ Can get specific run details
- ✅ Run status tracked independently

### AC4: Clean State Management
- ✅ Can mark project as "clean" (ready for new run)
- ✅ Can check if project needs cleanup
- ✅ Tracks modifications since last run

---

## Technical Details

### State Machine

```
[ACTIVE] ──run benchmark──> [ACTIVE with runs]
              │
              ├──success──> [COMPLETED]
              ├──failure──> [FAILED]
              └──archive──> [ARCHIVED]

[COMPLETED/FAILED] ──reset──> [ACTIVE]
[ANY] ──archive──> [ARCHIVED]
```

### Implementation

Add to `SandboxManager` class:

```python
def update_status(
    self,
    project_name: str,
    new_status: ProjectStatus,
    reason: Optional[str] = None,
) -> None:
    """Update project status with validation."""
    pass

def add_benchmark_run(
    self,
    project_name: str,
    run_id: str,
    config_file: str,
) -> BenchmarkRun:
    """Add new benchmark run to project."""
    pass

def get_run_history(self, project_name: str) -> List[BenchmarkRun]:
    """Get all benchmark runs for project."""
    pass

def is_clean(self, project_name: str) -> bool:
    """Check if project is in clean state."""
    pass

def mark_clean(self, project_name: str) -> None:
    """Mark project as clean (ready for new run)."""
    pass
```

---

## Testing Approach

### Unit Tests
- Test state transitions (valid and invalid)
- Test run tracking
- Test clean state management
- Test status queries with filters

### Expected Test Coverage
- State validation logic: 100%
- Run tracking: >90%
- Overall: >80%

---

## Definition of Done

- [ ] State transition logic implemented
- [ ] Run tracking implemented
- [ ] Clean state management implemented
- [ ] Unit tests written and passing
- [ ] State transitions validated correctly
- [ ] Invalid transitions raise errors
- [ ] Code reviewed and committed

---

## Related Stories

**Depends On**: Story 1.2
**Blocks**: Stories 1.4, 1.5, 1.6

---

**Estimated Completion**: 1 day
