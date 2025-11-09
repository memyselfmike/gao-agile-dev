# Story 29.1: Learning Schema Enhancement

**Epic**: Epic 29 - Self-Learning Feedback Loop
**Status**: Not Started
**Priority**: P0 (Critical)
**Estimated Effort**: 3 story points
**Owner**: Amelia (Developer)
**Created**: 2025-11-09
**Dependencies**: Epic 28 complete, Epics 22-27 (ceremony infrastructure)

---

## User Story

**As a** learning tracking system
**I want** enhanced schema with application metrics and rollback capability
**So that** I can track learning effectiveness over time and safely migrate

---

## Acceptance Criteria

### AC1: Database Migration Script (Migration 006)
- [ ] Create `migrations/migration_006_learning_application_tracking.py`
- [ ] Migration includes:
  - `migrate_up()` function to apply changes
  - `migrate_down()` function for rollback (C6 fix - table rebuild strategy)
  - `verify_migration()` function to validate state
  - Automatic database backup before migration
- [ ] Migration adds columns to `learning_index` table:
  - `application_count INTEGER DEFAULT 0` - How many times applied
  - `success_rate REAL DEFAULT 1.0` - Success rate (0.0-1.0)
  - `confidence_score REAL DEFAULT 0.5` - Confidence in learning (0.0-1.0)
  - `decay_factor REAL DEFAULT 1.0` - Recency decay (0.5-1.0)
- [ ] Migration creates new `learning_applications` table:
  ```sql
  CREATE TABLE learning_applications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      learning_id INTEGER NOT NULL REFERENCES learning_index(id),
      epic_num INTEGER,
      story_num INTEGER,
      outcome TEXT CHECK(outcome IN ('success', 'failure', 'partial')) NOT NULL,
      application_context TEXT,
      applied_at TEXT NOT NULL,
      metadata JSON,
      FOREIGN KEY (learning_id) REFERENCES learning_index(id),
      FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num)
  );
  ```
- [ ] Indexes created for performance:
  - `idx_learning_applications_learning_id` on `learning_id`
  - `idx_learning_applications_epic` on `epic_num`
  - `idx_learning_applications_applied_at` on `applied_at`
  - `idx_learning_index_category_active` on `category, is_active` (C6 gap analysis)
  - `idx_learning_index_relevance` on `relevance_score DESC` (C6 gap analysis)

### AC2: Rollback Capability (C6 Fix)
- [ ] Rollback strategy implemented using table rebuild (SQLite doesn't support DROP COLUMN)
- [ ] `migrate_down()` function:
  - Creates backup before rollback
  - Rebuilds `learning_index` table without new columns
  - Drops `learning_applications` table
  - Recreates original indexes
  - Validates rollback success
- [ ] Backup files created with timestamps:
  - Before migration: `documents.backup_{timestamp}.db`
  - Before rollback: `documents.rollback_backup_{timestamp}.db`
- [ ] CLI commands:
  ```bash
  python -m gao_dev.migrations.migration_006 up      # Apply migration
  python -m gao_dev.migrations.migration_006 verify  # Verify state
  python -m gao_dev.migrations.migration_006 down    # Rollback
  ```

### AC3: Migration Safety & Validation
- [ ] Migration validates preconditions:
  - `learning_index` table exists
  - Database is not locked
  - Sufficient disk space for backup
- [ ] Post-migration validation:
  - All new columns exist with correct types
  - All indexes created successfully
  - `learning_applications` table exists with correct schema
  - Foreign key constraints work
  - No data loss from existing `learning_index` records
- [ ] Error handling:
  - Transaction rollback on any failure
  - Clear error messages
  - Restore instructions in logs
- [ ] Dry-run mode available for testing

### AC4: Schema Documentation
- [ ] Update `docs/features/git-integrated-hybrid-wisdom/SCHEMA.md` with:
  - New columns in `learning_index` table
  - New `learning_applications` table structure
  - Indexes added
  - Foreign key relationships
  - Example queries for learning statistics
- [ ] Migration guide created at `docs/features/ceremony-integration-and-self-learning/MIGRATION_006.md`:
  - Why this migration is needed
  - What changes are made
  - How to apply the migration
  - How to rollback if needed
  - Performance impact (minimal)
  - Breaking changes (none)

### AC5: Default Values & Initialization
- [ ] New columns have safe defaults:
  - `application_count = 0` - No applications yet
  - `success_rate = 1.0` - Optimistic default (will adjust with data)
  - `confidence_score = 0.5` - Neutral confidence
  - `decay_factor = 1.0` - Full strength (freshly indexed)
- [ ] Existing learnings get default values automatically via ALTER TABLE
- [ ] No manual data migration needed

### AC6: Unit Tests
- [ ] `tests/migrations/test_migration_006.py` created with tests:
  - Migration up applies all changes successfully
  - Migration down rolls back all changes
  - Verify function correctly validates state
  - Backup creation works
  - Error handling triggers rollback
  - Existing data preserved during migration
  - Foreign key constraints enforced
  - Indexes improve query performance
- [ ] Test coverage >95%

---

## Technical Details

### File Structure
```
migrations/
   migration_006_learning_application_tracking.py  # Migration script (~300 lines)

docs/features/ceremony-integration-and-self-learning/
   MIGRATION_006.md                                # Migration guide (~150 lines)

tests/migrations/
   test_migration_006.py                           # Tests (~200 lines)
```

### Implementation Approach

**C6 Fix - Rollback Strategy**:
Since SQLite doesn't support `DROP COLUMN`, rollback uses table rebuild:
1. Create temporary table with old schema
2. Copy data (excluding new columns)
3. Drop original table
4. Rename temporary table
5. Recreate indexes
6. Validate

**Migration Flow**:
```python
def migrate_up(db_path: Path):
    # 1. Backup database
    backup_path = create_backup(db_path)

    with sqlite3.connect(db_path) as conn:
        try:
            # 2. Add columns to learning_index
            conn.execute("ALTER TABLE learning_index ADD COLUMN application_count INTEGER DEFAULT 0")
            conn.execute("ALTER TABLE learning_index ADD COLUMN success_rate REAL DEFAULT 1.0")
            conn.execute("ALTER TABLE learning_index ADD COLUMN confidence_score REAL DEFAULT 0.5")
            conn.execute("ALTER TABLE learning_index ADD COLUMN decay_factor REAL DEFAULT 1.0")

            # 3. Create learning_applications table
            conn.execute(CREATE_TABLE_SQL)

            # 4. Create indexes
            conn.execute(CREATE_INDEX_SQL)

            # 5. Validate
            verify_migration(db_path)

        except Exception as e:
            print(f"Migration failed: {e}")
            print(f"Restore from backup: {backup_path}")
            raise

def migrate_down(db_path: Path):
    # Rebuild table without new columns (see CRITICAL_FIXES.md C6)
    # ...
```

**Key Files to Create**:
1. `migrations/migration_006_learning_application_tracking.py` (~300 lines)
2. `docs/features/ceremony-integration-and-self-learning/MIGRATION_006.md` (~150 lines)
3. `tests/migrations/test_migration_006.py` (~200 lines)

**Key Considerations**:
- SQLite 3.35+ required for ALTER TABLE support (most systems have this)
- Backup before migration is critical
- Rollback must be tested thoroughly
- Migration is idempotent (can run multiple times safely)
- No downtime required (atomic transaction)

---

## Testing Strategy

### Unit Tests
- Migration up succeeds with clean database
- Migration down successfully rolls back
- Backup creation works correctly
- Verify function detects missing columns
- Verify function detects missing table
- Error triggers rollback
- Idempotency (running twice doesn't break)

### Integration Tests
- Apply migration to test database with existing learnings
- Verify all existing data preserved
- Verify new columns have correct defaults
- Test foreign key constraints work
- Test indexes improve query performance (query plan analysis)

### Manual Testing
```bash
# Test migration
cd C:\Projects\gao-agile-dev

# Apply migration
python -m gao_dev.migrations.migration_006 up

# Verify
python -m gao_dev.migrations.migration_006 verify

# Test rollback
python -m gao_dev.migrations.migration_006 down

# Verify rollback
python -m gao_dev.migrations.migration_006 verify  # Should fail (columns missing)
```

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Migration 006 script created and tested
- [ ] Rollback capability works (C6 fix validated)
- [ ] Backup strategy implemented
- [ ] Schema documentation updated
- [ ] Migration guide written
- [ ] Unit tests passing (>95% coverage)
- [ ] Integration tests passing
- [ ] No linting errors (ruff)
- [ ] Manual migration tested successfully
- [ ] Code reviewed and approved
- [ ] Changes committed with clear message
- [ ] Story marked as complete in sprint-status.yaml

---

## Dependencies

**Upstream**:
- Epic 24 (State tables & tracker) - `learning_index` table exists
- Epic 27 (Integration) - database schema stable

**Downstream**:
- Story 29.2 (LearningApplicationService) - needs new schema
- Story 29.6 (Learning Decay) - needs `decay_factor` column
- All other Epic 29 stories depend on this schema

---

## Notes

- **CRITICAL**: Test rollback thoroughly before production
- Migration is backward compatible (no breaking changes)
- Existing learnings work with default values
- Performance impact minimal (<100ms for 1000 learnings)
- C6 fix ensures safe rollback via table rebuild
- This is a foundational story - must complete before 29.2-29.7

---

## Related Documents

- PRD: `docs/features/ceremony-integration-and-self-learning/PRD.md`
- Architecture: `docs/features/ceremony-integration-and-self-learning/ARCHITECTURE.md` (Data Models section)
- Critical Fixes: `docs/features/ceremony-integration-and-self-learning/CRITICAL_FIXES.md` (C6 fix)
- Epic 29: `docs/features/ceremony-integration-and-self-learning/epics/epic-29-self-learning-feedback-loop.md`
