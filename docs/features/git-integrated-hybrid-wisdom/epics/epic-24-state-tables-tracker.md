# Epic 24: State Tables & Tracker

**Epic ID**: Epic-GHW-24
**Feature**: Git-Integrated Hybrid Wisdom Architecture
**Duration**: Week 3 (5 days)
**Owner**: Amelia (Developer)
**Status**: Planning
**Previous Epic**: Epic 22, Epic 23

---

## Epic Goal

Create database state tables and StateCoordinator service with specialized sub-services for fast state queries.

**Success Criteria**:
- Migration 005 runs successfully
- StateCoordinator facade created (~300 LOC)
- 5 specialized services created (~100 LOC each)
- Query performance <5ms
- 50+ unit tests passing

---

## Overview

This epic implements the database layer for fast state queries, building on the clean architecture from Epic 22 and the enhanced GitManager from Epic 23.

### Key Deliverables

1. **Migration 005**: Database schema with 5 new tables
   - epic_state
   - story_state
   - action_items
   - ceremony_summaries
   - learning_index

2. **StateCoordinator**: Facade coordinating state services

3. **5 Specialized Services** (~100 LOC each):
   - EpicStateService
   - StoryStateService
   - ActionItemService
   - CeremonyService
   - LearningIndexService

4. **Testing**: 50+ unit tests

---

## User Stories (7 stories)

### Story 24.1: Create Migration 005 (State Tables)
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Create database migration adding 5 state tracking tables with indexes.

**Acceptance Criteria**:
- [ ] Create migration file 005_add_state_tables.sql
- [ ] All 5 tables created with proper indexes
- [ ] Foreign key constraints defined
- [ ] Migration tested on clean database
- [ ] Migration tested on existing project
- [ ] 5 migration tests

---

### Story 24.2: Implement EpicStateService
**Priority**: P0 (Critical)
**Estimate**: 5 hours

**Description**:
Implement service for epic state management.

**Acceptance Criteria**:
- [ ] Service <150 LOC
- [ ] create(), update_progress(), archive() methods
- [ ] Query performance <5ms
- [ ] 10 unit tests

---

### Story 24.3: Implement StoryStateService
**Priority**: P0 (Critical)
**Estimate**: 5 hours

**Description**:
Implement service for story state management.

**Acceptance Criteria**:
- [ ] Service <150 LOC
- [ ] create(), transition(), complete() methods
- [ ] Query performance <5ms
- [ ] 10 unit tests

---

### Story 24.4: Implement ActionItemService
**Priority**: P1 (High)
**Estimate**: 4 hours

**Description**:
Implement service for action item tracking.

**Acceptance Criteria**:
- [ ] Service <100 LOC
- [ ] create(), complete(), get_active() methods
- [ ] Query performance <5ms
- [ ] 8 unit tests

---

### Story 24.5: Implement CeremonyService
**Priority**: P1 (High)
**Estimate**: 4 hours

**Description**:
Implement service for ceremony summary tracking.

**Acceptance Criteria**:
- [ ] Service <100 LOC
- [ ] create_summary(), get_recent() methods
- [ ] Query performance <5ms
- [ ] 8 unit tests

---

### Story 24.6: Implement LearningIndexService
**Priority**: P1 (High)
**Estimate**: 4 hours

**Description**:
Implement service for learning indexing.

**Acceptance Criteria**:
- [ ] Service <100 LOC
- [ ] index(), supersede(), search() methods
- [ ] Query performance <5ms
- [ ] 8 unit tests

---

### Story 24.7: Implement StateCoordinator Facade
**Priority**: P0 (Critical)
**Estimate**: 6 hours

**Description**:
Create StateCoordinator facade that coordinates all state services.

**Acceptance Criteria**:
- [ ] Facade <300 LOC
- [ ] Delegates to all 5 services
- [ ] Coordinated operations (e.g., create_story updates epic)
- [ ] Integration tests
- [ ] 12 integration tests

---

## Dependencies

**Upstream**: Epic 22 (clean architecture), Epic 23 (GitManager enhancements)

**Downstream**: Epic 25 (Git-Integrated State Manager uses these services)

---

## Technical Notes

### Database Schema

See `gao_dev/lifecycle/migrations/005_add_state_tables.sql` for full schema.

**Tables**:
- epic_state: Fast epic progress queries
- story_state: Fast story status queries
- action_items: Active action item tracking
- ceremony_summaries: Ceremony outcomes index
- learning_index: Topical learning index

### Service Architecture

```
StateCoordinator (facade)
    ↓
    ├─→ EpicStateService
    ├─→ StoryStateService
    ├─→ ActionItemService
    ├─→ CeremonyService
    └─→ LearningIndexService
```

---

## Testing Strategy

**Unit Tests**: 50+
- Migration tests: 5
- EpicStateService: 10
- StoryStateService: 10
- ActionItemService: 8
- CeremonyService: 8
- LearningIndexService: 8
- StateCoordinator: 12

**Performance**: All queries <5ms (benchmarked)

---

## Success Metrics

- [ ] All 5 tables created
- [ ] All 6 services implemented (<200 LOC each)
- [ ] Query performance <5ms
- [ ] 50+ tests passing
- [ ] Test coverage >80%

---

**Epic Status**: Planning (Awaiting Epic 22, 23 completion)
**Next Step**: Complete Epic 22 and Epic 23 first
**Created**: 2025-11-09
