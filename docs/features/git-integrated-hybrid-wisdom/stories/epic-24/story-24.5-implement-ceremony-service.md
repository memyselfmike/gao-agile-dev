# Story 24.5: Implement CeremonyService

**Epic**: Epic 24 - State Tables & Tracker
**Story ID**: 24.5
**Priority**: P1
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement CeremonyService for recording ceremony summaries (stand-ups, retrospectives, planning sessions) with links to full transcripts and action items created.

---

## Acceptance Criteria

- [ ] Service <100 LOC
- [ ] Methods: create_summary(), get_recent(), get_by_type()
- [ ] Support ceremony types (standup, retrospective, planning, review)
- [ ] Track participants, outcomes, action items count
- [ ] Link to full transcript documents
- [ ] All queries <5ms
- [ ] 8 unit tests

---

## Technical Approach

### Files to Create

- `gao_dev/core/services/ceremony_service.py` (~90 LOC)
- `tests/core/state/test_ceremony_service.py` (~120 LOC)

### Key Methods

```python
class CeremonyService:
    def create_summary(self, ceremony_type: str, epic_num: int, participants: List[str],
                      outcomes: List[str], doc_id: int) -> int
    def get_recent(self, epic_num: Optional[int] = None, limit: int = 10) -> List[Dict]
    def get_by_type(self, ceremony_type: str) -> List[Dict]
```

---

## Testing Strategy

- test_create_ceremony_summary()
- test_get_recent_ceremonies()
- test_get_by_type()
- test_filter_by_epic()
- test_link_to_transcript_document()
- test_participants_json_array()
- test_outcomes_json_array()
- test_query_performance()

---

## Dependencies

**Upstream**: Story 24.1
**Downstream**: Epic 26 (ceremonies use this service)

---

## Definition of Done

- [ ] All criteria met
- [ ] 8 tests passing
- [ ] Service <100 LOC
- [ ] Git commit: "feat(epic-24): implement CeremonyService"

---

**Created**: 2025-11-09
