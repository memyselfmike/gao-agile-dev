# Story 26.7: Real-Time Context Loading

**Epic**: Epic 26 - Multi-Agent Ceremonies
**Story ID**: 26.7
**Priority**: P0
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Integrate FastContextLoader for ceremony context with <5ms performance. Ceremonies use get_epic_context() and agent-specific context loading.

---

## Acceptance Criteria

- [ ] Ceremonies use FastContextLoader.get_epic_context()
- [ ] Agent-specific context loaded (get_agent_context)
- [ ] Context refresh during ceremony (if long-running)
- [ ] Performance <5ms (benchmarked)
- [ ] 6 performance tests

---

## Files to Modify

- `gao_dev/orchestrator/ceremony_orchestrator.py` (+~30 LOC)
- `tests/performance/test_ceremony_context_performance.py` (new, ~80 LOC)

---

## Definition of Done

- [ ] 6 tests passing
- [ ] Performance <5ms
- [ ] Git commit: "feat(epic-26): integrate real-time context loading for ceremonies"

---

**Created**: 2025-11-09
