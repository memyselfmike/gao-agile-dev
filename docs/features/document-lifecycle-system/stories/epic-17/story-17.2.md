# Story 17.2: Database Unification (Epic 15)

**Epic:** 17 - Context System Integration
**Story Points:** 5
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Unify all context tables into single database with Epic 15 StateTracker to fix database fragmentation. Currently, Epic 16 context tables exist in separate databases, creating management overhead and preventing foreign key relationships with workflow execution state. This story consolidates all tables into a single `gao_dev.db` database with proper foreign key constraints, enabling referential integrity and simplified database management.

---

## Business Value

This story eliminates database fragmentation and enables data integrity:

- **Unified Management**: Single database simplifies backup, migration, and maintenance
- **Referential Integrity**: Foreign keys prevent orphaned context data
- **Data Consistency**: All GAO-Dev data in one place ensures consistency
- **Query Performance**: Single DB enables cross-table queries and analytics
- **Migration Simplicity**: Single migration path instead of multiple databases
- **Developer Experience**: One connection, one schema, simpler code
- **Production Ready**: Enterprise-grade data integrity with FK constraints
- **Troubleshooting**: Easier to debug with all data in one database
- **Observability**: Single database for comprehensive system monitoring
- **Foundation for Analytics**: Unified data enables advanced analytics and reporting

---

## Acceptance Criteria

### Database Unification
- [ ] Single `gao_dev.db` contains all tables (state, context, documents)
- [ ] `workflow_context` table in unified database
- [ ] `context_usage` table in unified database
- [ ] `context_lineage` table in unified database
- [ ] All Epic 15 state tables in same database
- [ ] No separate context-specific databases exist

### Foreign Key Constraints
- [ ] Foreign keys between `context_usage` and `workflow_context` validated
- [ ] Foreign keys between `context_usage` and `documents` table validated
- [ ] Foreign key: `workflow_context.workflow_id` -> `workflow_executions.id`
- [ ] Foreign key: `context_usage.context_id` -> `workflow_context.id`
- [ ] Foreign key: `context_lineage.parent_id` -> `workflow_context.id`
- [ ] Foreign key: `context_lineage.child_id` -> `workflow_context.id`
- [ ] FK constraints enforced (CASCADE on delete where appropriate)

### Configuration
- [ ] ContextPersistence uses same DB path as StateTracker
- [ ] ContextUsageTracker uses same DB path
- [ ] ContextLineageTracker uses same DB path
- [ ] Shared DB path configured via `get_gao_db_path()` function
- [ ] All context modules import from shared config

### Migration
- [ ] Migration script moves data from old separate DBs
- [ ] Migration script validates data integrity
- [ ] Migration logs show successful data transfer
- [ ] No data loss during migration
- [ ] No orphaned data in separate databases
- [ ] Old separate DB files archived (not deleted immediately)

### Testing
- [ ] Integration tests verify FK constraints work
- [ ] Test cascade delete behavior
- [ ] Test orphan prevention (FK violations rejected)
- [ ] Test unified DB queries work correctly
- [ ] Test migration script with test data

---

## Technical Notes

### Implementation Approach

**File:** `gao_dev/core/config.py`

Create unified database path function:

```python
from pathlib import Path

def get_gao_db_path() -> Path:
    """
    Get path to unified GAO-Dev database.

    Returns:
        Path to gao_dev.db (single unified database)
    """
    # Use project root or ~/.gao-dev/ for database
    project_root = Path.cwd()
    db_path = project_root / ".gao-dev" / "gao_dev.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path
```

**File:** `gao_dev/core/context/persistence.py`

Update ContextPersistence to use unified DB:

```python
from gao_dev.core.config import get_gao_db_path

class ContextPersistence:
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize ContextPersistence.

        Args:
            db_path: Path to database (uses unified DB if None)
        """
        self.db_path = db_path or get_gao_db_path()
        self._init_database()
```

**File:** `gao_dev/core/context/migrations/003_unify_database.sql`

Create migration script:

```sql
-- Migration 003: Unify context tables into single database
-- Adds foreign key constraints for referential integrity

-- Add foreign key constraints to workflow_context
CREATE TABLE IF NOT EXISTS workflow_context_new (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    epic_number INTEGER,
    story_number INTEGER,
    phase TEXT NOT NULL,
    status TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES workflow_executions(id) ON DELETE CASCADE
);

-- Copy data from old table
INSERT INTO workflow_context_new
SELECT * FROM workflow_context;

-- Replace old table
DROP TABLE workflow_context;
ALTER TABLE workflow_context_new RENAME TO workflow_context;

-- Add foreign key constraints to context_usage
CREATE TABLE IF NOT EXISTS context_usage_new (
    id TEXT PRIMARY KEY,
    context_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    document_type TEXT NOT NULL,
    document_id TEXT,
    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (context_id) REFERENCES workflow_context(id) ON DELETE CASCADE
);

-- Copy data from old table
INSERT INTO context_usage_new
SELECT * FROM context_usage;

-- Replace old table
DROP TABLE context_usage;
ALTER TABLE context_usage_new RENAME TO context_usage;

-- Add foreign key constraints to context_lineage
CREATE TABLE IF NOT EXISTS context_lineage_new (
    id TEXT PRIMARY KEY,
    parent_id TEXT NOT NULL,
    child_id TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES workflow_context(id) ON DELETE CASCADE,
    FOREIGN KEY (child_id) REFERENCES workflow_context(id) ON DELETE CASCADE
);

-- Copy data from old table
INSERT INTO context_lineage_new
SELECT * FROM context_lineage;

-- Replace old table
DROP TABLE context_lineage;
ALTER TABLE context_lineage_new RENAME TO context_lineage;

-- Create indexes for foreign keys
CREATE INDEX IF NOT EXISTS idx_workflow_context_workflow_id ON workflow_context(workflow_id);
CREATE INDEX IF NOT EXISTS idx_context_usage_context_id ON context_usage(context_id);
CREATE INDEX IF NOT EXISTS idx_context_lineage_parent ON context_lineage(parent_id);
CREATE INDEX IF NOT EXISTS idx_context_lineage_child ON context_lineage(child_id);
```

**Files to Modify:**
- `gao_dev/core/config.py` - Add `get_gao_db_path()` function
- `gao_dev/core/context/persistence.py` - Use unified DB path
- `gao_dev/core/context/usage_tracker.py` - Use unified DB path
- `gao_dev/core/context/lineage_tracker.py` - Use unified DB path

**Files to Create:**
- `gao_dev/core/context/migrations/003_unify_database.sql` - Migration script
- `tests/core/context/test_database_unification.py` - Integration tests

**Dependencies:**
- Epic 15 (StateTracker with gao_dev.db)
- Story 16.2, 16.3, 16.4 (Context tables)

---

## Testing Requirements

### Integration Tests

**Database Unification:**
- [ ] Test all context tables in single database
- [ ] Test shared database with state tables
- [ ] Test database path configuration
- [ ] Test all modules use same database

**Foreign Key Constraints:**
- [ ] Test FK constraint: workflow_context -> workflow_executions
- [ ] Test FK constraint: context_usage -> workflow_context
- [ ] Test FK constraint: context_lineage -> workflow_context
- [ ] Test FK violation rejected (orphan prevention)
- [ ] Test cascade delete removes related records

**Migration:**
- [ ] Test migration moves data from separate DBs
- [ ] Test migration preserves all data
- [ ] Test migration validates FK constraints
- [ ] Test migration is idempotent (can run multiple times)
- [ ] Test migration logs success/failure

**Cross-Table Queries:**
- [ ] Test query workflow context with execution state
- [ ] Test query context usage with lineage
- [ ] Test join workflow_context and context_usage
- [ ] Test analytics queries across all tables

### Unit Tests
- [ ] Test `get_gao_db_path()` returns correct path
- [ ] Test DB path creates .gao-dev directory
- [ ] Test ContextPersistence uses unified DB
- [ ] Test ContextUsageTracker uses unified DB
- [ ] Test ContextLineageTracker uses unified DB

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Update database architecture documentation
- [ ] Document foreign key constraints and relationships
- [ ] Add ER diagram showing all tables and FKs
- [ ] Document migration process and script
- [ ] Add troubleshooting guide for FK violations
- [ ] Update configuration documentation with `get_gao_db_path()`
- [ ] Document database backup procedures
- [ ] Add examples of cross-table queries

---

## Implementation Details

### Development Approach

**Phase 1: Configuration**
1. Create `get_gao_db_path()` in config.py
2. Update all context modules to use shared config
3. Test unified DB path works correctly

**Phase 2: Schema Updates**
1. Create migration script with FK constraints
2. Add indexes for foreign key columns
3. Test migration script with test data

**Phase 3: Migration**
1. Run migration on development database
2. Verify all FK constraints work
3. Test cascade delete behavior
4. Archive old separate databases

**Phase 4: Testing**
1. Write integration tests for unified DB
2. Test FK constraints and violations
3. Test cross-table queries
4. Verify no orphaned data

### Quality Gates
- [ ] All integration tests pass
- [ ] Foreign key constraints enforced
- [ ] Migration script tested and verified
- [ ] No data loss during migration
- [ ] Cross-table queries work correctly
- [ ] Documentation updated with ER diagram

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Single `gao_dev.db` contains all tables
- [ ] `get_gao_db_path()` function implemented
- [ ] All context modules use unified database
- [ ] Foreign key constraints added and enforced
- [ ] Migration script `003_unify_database.sql` created
- [ ] Migration tested with real data (no data loss)
- [ ] Integration tests pass (>80% coverage)
- [ ] Cross-table queries working correctly
- [ ] ER diagram created and documented
- [ ] Code reviewed and approved
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-17): implement Story 17.2 - Database Unification

  - Create get_gao_db_path() for unified database configuration
  - Unify all context tables into single gao_dev.db
  - Add foreign key constraints (workflow_context, context_usage, lineage)
  - Create migration script 003_unify_database.sql
  - Update all context modules to use shared DB path
  - Add indexes for foreign key columns
  - Implement cascade delete for referential integrity
  - Add integration tests for FK constraints
  - Create ER diagram showing all tables and relationships

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
