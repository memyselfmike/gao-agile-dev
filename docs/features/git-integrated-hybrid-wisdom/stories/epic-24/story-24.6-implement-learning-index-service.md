# Story 24.6: Implement LearningIndexService

**Epic**: Epic 24 - State Tables & Tracker
**Story ID**: 24.6
**Priority**: P1
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement LearningIndexService for indexing and searching learnings by topic with support for superseded learnings (when new learnings replace old ones).

---

## Acceptance Criteria

- [ ] Service <100 LOC
- [ ] Methods: index(), supersede(), search(), get_active()
- [ ] Topic-based searching with relevance filtering
- [ ] Support for marking learnings as obsolete (superseded_by)
- [ ] Link learnings to source documents
- [ ] All queries <5ms
- [ ] 8 unit tests

---

## Technical Approach

### Files to Create

- `gao_dev/core/services/learning_index_service.py` (~90 LOC)
- `tests/core/state/test_learning_index_service.py` (~120 LOC)

### Key Methods

```python
class LearningIndexService:
    def index(self, topic: str, summary: str, relevance: str, contributor: str,
             source_doc_id: int) -> int
    def supersede(self, old_learning_id: int, new_learning_id: int) -> None
    def search(self, topic: str, relevance: str = "high") -> List[Dict]
    def get_active(self, limit: int = 20) -> List[Dict]
```

---

## Testing Strategy

- test_index_learning()
- test_supersede_learning()
- test_search_by_topic()
- test_search_by_relevance()
- test_get_active_learnings()
- test_superseded_learnings_excluded()
- test_link_to_source_document()
- test_query_performance()

---

## Dependencies

**Upstream**: Story 24.1
**Downstream**: Epic 26 (retrospectives create learnings)

---

## Definition of Done

- [ ] All criteria met
- [ ] 8 tests passing
- [ ] Service <100 LOC
- [ ] Git commit: "feat(epic-24): implement LearningIndexService"

---

**Created**: 2025-11-09
