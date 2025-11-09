# Story 24.3: Implement StoryStateService

**Epic**: Epic 24 - State Tables & Tracker
**Story ID**: 24.3
**Priority**: P0
**Estimate**: 5 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement StoryStateService for managing story state lifecycle in the story_state table (todo → in_progress → review → done).

---

## Acceptance Criteria

- [ ] Service <150 LOC
- [ ] Methods: create(), transition(), complete(), get()
- [ ] State transitions validated (todo → in_progress → review → done)
- [ ] Timestamps tracked (created_at, started_at, completed_at)
- [ ] All queries <5ms
- [ ] 10 unit tests

---

## Technical Approach

### Files to Create

- `gao_dev/core/services/story_state_service.py` (~130 LOC)
- `tests/core/state/test_story_state_service.py` (~150 LOC)

### Key Methods

```python
class StoryStateService:
    def create(self, story_id: str, epic_num: int, title: str, estimate: float) -> None
    def transition(self, story_id: str, new_state: str) -> int  # Returns epic_num
    def complete(self, story_id: str, actual_hours: float) -> int
    def get(self, story_id: str) -> Optional[Dict]
```

---

## Testing Strategy

- test_create_story_state()
- test_transition_to_in_progress()
- test_transition_to_done()
- test_complete_story()
- test_invalid_transition_raises_error()
- test_get_story_state()
- test_create_duplicate_story_raises_error()
- test_transition_nonexistent_story_raises_error()
- test_timestamps_set_correctly()
- test_query_performance()

---

## Dependencies

**Upstream**: Story 24.1 (story_state table)
**Downstream**: Story 24.7 (StateCoordinator)

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] 10 tests passing
- [ ] Service <150 LOC
- [ ] Git commit: "feat(epic-24): implement StoryStateService"

---

**Created**: 2025-11-09
