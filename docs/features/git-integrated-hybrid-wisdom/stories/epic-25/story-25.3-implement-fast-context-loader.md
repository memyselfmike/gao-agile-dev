# Story 25.3: Implement FastContextLoader

**Epic**: Epic 25 - Git-Integrated State Manager
**Story ID**: 25.3
**Priority**: P0
**Estimate**: 8 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Implement FastContextLoader for <5ms context queries using database indexes. Provides get_epic_context(), get_agent_context(), and analyze_existing_project().

---

## Acceptance Criteria

- [ ] Service ~400 LOC
- [ ] get_epic_context(epic_num) <5ms
- [ ] get_agent_context(agent, epic) <5ms (role-specific)
- [ ] analyze_existing_project() <10ms
- [ ] Uses json_group_array() for aggregation
- [ ] Limits results (max 20 action items, 10 learnings)
- [ ] 15 unit tests + 5 performance benchmarks

---

## Files to Create

- `gao_dev/core/services/fast_context_loader.py` (~400 LOC)
- `tests/core/services/test_fast_context_loader.py` (~250 LOC)

---

## Key Methods

```python
class FastContextLoader:
    def get_epic_context(self, epic_num: int) -> EpicContext:
        """Complete epic context in <5ms."""

    def get_agent_context(self, agent: str, epic: int) -> Dict:
        """Agent-specific context in <5ms."""

    def analyze_existing_project(self, path: Path) -> ProjectState:
        """Project analysis in <10ms."""
```

---

## Testing Strategy

- 15 unit tests (functionality)
- 5 performance benchmarks (<5ms validation)

---

## Definition of Done

- [ ] 20 tests passing
- [ ] Performance <5ms (benchmarked)
- [ ] Service ~400 LOC
- [ ] Git commit: "feat(epic-25): implement FastContextLoader"

---

**Created**: 2025-11-09
