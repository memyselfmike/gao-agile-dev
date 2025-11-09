# Story 24.1: Create Migration 005 (State Tables)

**Epic**: Epic 24 - State Tables & Tracker
**Story ID**: 24.1
**Priority**: P0
**Estimate**: 6 hours
**Owner**: Amelia
**Status**: Todo

---

## Story Description

Create database migration 005 adding five state tracking tables with proper indexes, foreign keys, and constraints. This migration establishes the database schema for fast state queries (<5ms) that support the hybrid architecture.

The migration creates tables for epic_state, story_state, action_items, ceremony_summaries, and learning_index. These tables enable instant project status queries without reading Markdown files, supporting Epic 26 ceremonies with real-time context loading.

---

## Acceptance Criteria

- [ ] Create `gao_dev/lifecycle/migrations/005_add_state_tables.sql` file
- [ ] All 5 tables created with proper column types and constraints
- [ ] All foreign key constraints defined (story_state → epic_state, etc.)
- [ ] Indexes created on all foreign keys and common query columns
- [ ] CHECK constraints for state enums (planning, active, complete, etc.)
- [ ] Migration tested on clean database (pytest)
- [ ] Migration tested on existing project (idempotent)
- [ ] 5 migration tests (one per table validation)
- [ ] Migration follows existing migration pattern (001-004)

---

## Technical Approach

### Files to Create

- `gao_dev/lifecycle/migrations/005_add_state_tables.sql` (~100 LOC)
  - 5 CREATE TABLE statements
  - 12+ CREATE INDEX statements
  - Foreign key constraints

- `tests/core/state/test_migration_005.py` (~80 LOC)
  - 5 tests validating each table creation
  - Test migration on clean DB
  - Test migration idempotency

### Database Schema

**epic_state** (~20 LOC):
```sql
CREATE TABLE epic_state (
    epic_num INTEGER PRIMARY KEY,
    epic_title TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('planning', 'active', 'complete', 'archived')),
    total_stories INTEGER NOT NULL DEFAULT 0,
    completed_stories INTEGER NOT NULL DEFAULT 0,
    in_progress_stories INTEGER NOT NULL DEFAULT 0,
    progress_percent REAL NOT NULL DEFAULT 0,
    current_story TEXT,
    start_date TEXT,
    target_date TEXT,
    actual_completion_date TEXT,
    metadata JSON
);
CREATE INDEX idx_epic_state_state ON epic_state(state);
```

**story_state** (~22 LOC):
```sql
CREATE TABLE story_state (
    story_id TEXT PRIMARY KEY,
    epic_num INTEGER NOT NULL REFERENCES epic_state(epic_num),
    story_title TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('todo', 'in_progress', 'review', 'done')),
    assignee TEXT,
    estimate_hours REAL,
    actual_hours REAL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    metadata JSON
);
CREATE INDEX idx_story_state_epic ON story_state(epic_num);
CREATE INDEX idx_story_state_state ON story_state(state);
CREATE INDEX idx_story_state_assignee ON story_state(assignee);
```

**action_items, ceremony_summaries, learning_index** (similar structure, ~50 LOC total)

---

## Testing Strategy

### Unit Tests (5 tests)

- test_migration_005_creates_epic_state() - Validates epic_state table structure
- test_migration_005_creates_story_state() - Validates story_state table structure
- test_migration_005_creates_action_items() - Validates action_items table structure
- test_migration_005_creates_ceremony_summaries() - Validates ceremony_summaries structure
- test_migration_005_creates_learning_index() - Validates learning_index structure

---

## Dependencies

**Upstream**: Epic 23 (GitManager for migration commits)

**Downstream**:
- Stories 24.2-24.7 (all services require these tables)
- Epic 25 (GitIntegratedStateManager writes to these tables)

---

## Implementation Notes

See ARCHITECTURE.md for complete schema definitions. Migration must be idempotent (safe to run multiple times).

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All 5 tests passing
- [ ] Migration runs successfully
- [ ] Code review completed
- [ ] Git commit: "feat(epic-24): add migration 005 for state tracking tables"

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
