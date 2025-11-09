# Story 24.2: Implement EpicStateService

**Epic**: Epic 24 - State Tables & Tracker
**Story ID**: 24.2
**Priority**: P0
**Estimate**: 5 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement EpicStateService for managing epic state in the epic_state table. This service provides create, update_progress, and archive methods with <5ms query performance.

The service follows the Single Responsibility Principle with <150 LOC and handles all epic state operations: creating epics, updating progress as stories complete, and archiving finished epics. It's used by StateCoordinator (Story 24.7) and GitIntegratedStateManager (Epic 25).

---

## Acceptance Criteria

- [ ] Service <150 LOC (adheres to SRP)
- [ ] `create(epic_num, title, metadata)` method creates epic_state record
- [ ] `update_progress(epic_num)` method recalculates progress from stories
- [ ] `archive(epic_num)` method transitions epic to archived state
- [ ] `get(epic_num)` method returns epic state Dict
- [ ] All queries <5ms (indexed)
- [ ] Comprehensive docstrings
- [ ] 10 unit tests covering all methods

---

## Technical Approach

### Files to Create

- `gao_dev/core/services/epic_state_service.py` (~120 LOC)
  - EpicStateService class
  - Methods: create(), update_progress(), archive(), get()

- `tests/core/state/test_epic_state_service.py` (~150 LOC)
  - 10 unit tests for epic state operations

### Key Methods

```python
class EpicStateService:
    def __init__(self, registry: DocumentRegistry):
        self.registry = registry

    def create(self, epic_num: int, title: str, metadata: Dict = None) -> None:
        """Create epic_state record."""

    def update_progress(self, epic_num: int) -> None:
        """Recalculate progress from story_state counts."""

    def archive(self, epic_num: int) -> None:
        """Transition epic to archived state."""

    def get(self, epic_num: int) -> Optional[Dict]:
        """Retrieve epic state."""
```

---

## Testing Strategy

### Unit Tests (10 tests)

- test_create_epic_state()
- test_update_progress_calculates_correctly()
- test_archive_epic()
- test_get_epic_state()
- test_create_duplicate_epic_raises_error()
- test_update_nonexistent_epic_raises_error()
- test_progress_calculation_with_no_stories()
- test_progress_calculation_with_mixed_states()
- test_get_nonexistent_epic_returns_none()
- test_epic_state_query_performance()

---

## Dependencies

**Upstream**: Story 24.1 (epic_state table must exist)
**Downstream**: Story 24.7 (StateCoordinator uses this service)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All 10 tests passing
- [ ] Service <150 LOC
- [ ] Query performance <5ms (benchmarked)
- [ ] Code review completed
- [ ] Git commit: "feat(epic-24): implement EpicStateService"

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
