# Story 24.7: Implement StateCoordinator Facade

**Epic**: Epic 24 - State Tables & Tracker
**Story ID**: 24.7
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement StateCoordinator as a facade that coordinates all 5 state services (EpicState, StoryState, ActionItem, Ceremony, LearningIndex). The facade provides high-level operations that coordinate multiple services atomically.

---

## Acceptance Criteria

- [ ] Facade <300 LOC (delegates to services)
- [ ] Coordinates create_story() to update both story_state and epic_state
- [ ] Coordinates transition_story() to update story and recalculate epic progress
- [ ] Provides unified interface to all 5 services
- [ ] All operations maintain consistency across tables
- [ ] Comprehensive docstrings
- [ ] 12 integration tests

---

## Technical Approach

### Files to Create

- `gao_dev/core/services/state_coordinator.py` (~280 LOC)
- `tests/core/state/test_state_coordinator.py` (~200 LOC)

### Key Structure

```python
class StateCoordinator:
    def __init__(self, registry: DocumentRegistry):
        self.registry = registry
        self.epics = EpicStateService(registry)
        self.stories = StoryStateService(registry)
        self.actions = ActionItemService(registry)
        self.ceremonies = CeremonyService(registry)
        self.learnings = LearningIndexService(registry)

    def create_story(self, story_id: str, epic_num: int, title: str, estimate: float) -> None:
        """Create story and update epic totals."""
        self.stories.create(story_id, epic_num, title, estimate)
        self.epics.update_progress(epic_num)

    def transition_story(self, story_id: str, new_state: str) -> None:
        """Transition story and update epic progress."""
        epic_num = self.stories.transition(story_id, new_state)
        self.epics.update_progress(epic_num)
```

---

## Testing Strategy

- test_create_epic()
- test_create_story_updates_epic()
- test_transition_story_updates_epic()
- test_complete_story_updates_epic()
- test_create_action_item()
- test_create_ceremony_summary()
- test_index_learning()
- test_get_epic_context()
- test_get_story_context()
- test_coordinated_operations_atomic()
- test_service_delegation()
- test_integration_with_all_services()

---

## Dependencies

**Upstream**: Stories 24.2-24.6 (all services)
**Downstream**: Epic 25 (GitIntegratedStateManager uses StateCoordinator)

---

## Definition of Done

- [ ] All criteria met
- [ ] 12 tests passing
- [ ] Facade <300 LOC
- [ ] All services integrated
- [ ] Git commit: "feat(epic-24): implement StateCoordinator facade"

---

**Created**: 2025-11-09
