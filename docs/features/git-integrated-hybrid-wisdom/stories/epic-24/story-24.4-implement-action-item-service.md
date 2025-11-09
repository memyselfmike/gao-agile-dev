# Story 24.4: Implement ActionItemService

**Epic**: Epic 24 - State Tables & Tracker
**Story ID**: 24.4
**Priority**: P1
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement ActionItemService for creating and tracking action items from ceremonies and retrospectives. Action items link to source documents (ceremonies) and support priority/assignee filtering.

---

## Acceptance Criteria

- [ ] Service <100 LOC
- [ ] Methods: create(), complete(), get_active(), get_by_assignee()
- [ ] Priority support (low, medium, high, critical)
- [ ] Link action items to source documents (ceremony summaries)
- [ ] All queries <5ms
- [ ] 8 unit tests

---

## Technical Approach

### Files to Create

- `gao_dev/core/services/action_item_service.py` (~90 LOC)
- `tests/core/state/test_action_item_service.py` (~120 LOC)

### Key Methods

```python
class ActionItemService:
    def create(self, summary: str, assignee: str, priority: str, source_doc_id: int) -> int
    def complete(self, action_id: int) -> None
    def get_active(self, epic_num: Optional[int] = None) -> List[Dict]
    def get_by_assignee(self, assignee: str) -> List[Dict]
```

---

## Testing Strategy

- test_create_action_item()
- test_complete_action_item()
- test_get_active_action_items()
- test_get_by_assignee()
- test_filter_by_epic()
- test_priority_ordering()
- test_link_to_source_document()
- test_query_performance()

---

## Dependencies

**Upstream**: Story 24.1
**Downstream**: Story 26.2 (ceremonies create action items)

---

## Definition of Done

- [ ] All criteria met
- [ ] 8 tests passing
- [ ] Service <100 LOC
- [ ] Git commit: "feat(epic-24): implement ActionItemService"

---

**Created**: 2025-11-09
