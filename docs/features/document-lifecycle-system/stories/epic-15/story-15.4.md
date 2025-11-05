# Story 15.4: Query Builder & API

**Epic:** 15 - State Tracking Database
**Story Points:** 4 | **Priority:** P1 | **Status:** Pending | **Owner:** TBD | **Sprint:** TBD

---

## Story Description

Implement query builder for complex state queries with intuitive API. Provide convenience methods for common queries.

---

## Acceptance Criteria

### Convenience Methods
- [ ] `get_stories_by_status(status)` with optional epic filter
- [ ] `get_epic_progress(epic_num)` returns {completed, total, percentage}
- [ ] `get_sprint_velocity(sprint_num)` returns points completed
- [ ] `get_blocked_stories()` returns all blocked stories
- [ ] `get_stories_needing_review()` based on criteria

### Query Optimization
- [ ] All queries use indexes (EXPLAIN QUERY PLAN verified)
- [ ] Query performance <50ms
- [ ] Result pagination support
- [ ] Limit result set size

### Result Formatting
- [ ] Return typed models (Story, Epic, Sprint dataclasses)
- [ ] Not raw SQL rows
- [ ] Support for dict output (for JSON APIs)

**Files to Create:**
- `gao_dev/core/state/query_builder.py`
- `tests/core/state/test_query_builder.py`

**Dependencies:** Story 15.2 (StateTracker)

---

## Definition of Done

- [ ] All convenience methods implemented
- [ ] Query optimization verified
- [ ] Tests passing
- [ ] Committed with atomic commit
