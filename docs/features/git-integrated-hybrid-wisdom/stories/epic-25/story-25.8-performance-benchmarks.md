# Story 25.8: Performance Benchmarks

**Epic**: Epic 25 - Git-Integrated State Manager
**Story ID**: 25.8
**Priority**: P1
**Estimate**: 4 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Create performance benchmarks validating all performance targets: epic context <5ms, story operations <100ms.

---

## Acceptance Criteria

- [ ] Epic context <5ms (p95)
- [ ] Agent context <5ms (p95)
- [ ] Story creation <100ms (including git commit)
- [ ] Story transition <50ms (including git commit)
- [ ] Project analysis <10ms
- [ ] 10 benchmark tests

---

## Files to Create

- `tests/performance/test_state_manager_performance.py` (~150 LOC)

---

## Benchmarks

- benchmark_epic_context()
- benchmark_agent_context()
- benchmark_create_story()
- benchmark_transition_story()
- benchmark_project_analysis()
- + 5 more

---

## Definition of Done

- [ ] All benchmarks passing (targets met)
- [ ] Git commit: "test(epic-25): add performance benchmarks"

---

**Created**: 2025-11-09
