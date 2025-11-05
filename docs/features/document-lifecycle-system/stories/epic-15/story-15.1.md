# Story 15.1: State Database Schema

**Epic:** 15 - State Tracking Database
**Story Points:** 5 | **Priority:** P0 | **Status:** Pending | **Owner:** TBD | **Sprint:** TBD

---

## Story Description

Create comprehensive SQLite schema for epics, stories, sprints, and workflow executions. This unified schema enables queryable state tracking to replace fragmented markdown and YAML files, providing a single source of truth for all project state with full audit trails and performance optimization.

---

## Business Value

This story provides the foundational database that transforms project state management:

- **Single Source of Truth**: Replaces fragmented markdown/YAML files with queryable database
- **Performance**: Sub-50ms queries for all state lookups replace slow file parsing
- **Audit Trail**: Complete history of state changes with timestamps and actors
- **Analytics**: Enable sprint velocity, burndown charts, and progress tracking
- **Scalability**: Handle 1000+ stories without performance degradation
- **Reliability**: ACID guarantees prevent data corruption and race conditions
- **Integration**: Prepares for markdown sync, CLI commands, and agent workflows

---

## Acceptance Criteria

### Epics Table
- [ ] `epics` table created with all fields:
  - Core: id, epic_num (UNIQUE), name, feature, goal, description
  - Status: status (planned/active/completed/cancelled)
  - Points: total_points, completed_points (auto-calculated)
  - Dates: created_at, started_at, completed_at, updated_at
  - Ownership: owner, created_by
  - Metadata: file_path, content_hash, metadata (JSON)
- [ ] CHECK constraint on status values
- [ ] Trigger for auto-updating updated_at timestamp
- [ ] Trigger for auto-calculating completed_points from stories
- [ ] Unit tests for epic table operations

### Stories Table
- [ ] `stories` table created with all fields:
  - Core: id, epic_num (FK), story_num, title, description
  - Status: status (pending/in_progress/done/blocked/cancelled)
  - Priority: priority (P0/P1/P2/P3)
  - Points: points (story points estimate)
  - Ownership: owner, created_by
  - Dates: created_at, started_at, completed_at, updated_at, due_date
  - Files: file_path, content_hash
  - Metadata: metadata (JSON), tags (JSON array)
- [ ] UNIQUE constraint on (epic_num, story_num)
- [ ] Foreign key to epics table with CASCADE update
- [ ] CHECK constraints on status and priority
- [ ] Trigger for auto-updating updated_at timestamp
- [ ] Trigger for updating epic.completed_points when story status changes
- [ ] Unit tests for story table operations

### Sprints Table
- [ ] `sprints` table created with all fields:
  - Core: id, sprint_num (UNIQUE), name, goal
  - Status: status (planned/active/completed/cancelled)
  - Dates: start_date, end_date, created_at, updated_at
  - Metrics: planned_points, completed_points, velocity
  - Metadata: metadata (JSON)
- [ ] CHECK constraint on status values
- [ ] CHECK constraint: end_date > start_date
- [ ] Trigger for auto-updating updated_at timestamp
- [ ] Trigger for auto-calculating completed_points from assigned stories
- [ ] Unit tests for sprint table operations

### Story Assignments Table
- [ ] `story_assignments` table for many-to-many relationship:
  - Fields: sprint_num (FK), epic_num (FK), story_num (FK), assigned_at
  - Composite primary key on (sprint_num, epic_num, story_num)
  - Foreign keys to sprints and stories with CASCADE delete
- [ ] Trigger for updating sprint.completed_points on assignment
- [ ] Unit tests for assignment operations

### Workflow Executions Table
- [ ] `workflow_executions` table created:
  - Core: id, workflow_name, phase
  - Story link: epic_num (FK), story_num (FK)
  - Status: status (started/running/completed/failed/cancelled)
  - Execution: executor (agent name), started_at, completed_at, duration_ms
  - Results: output, error_message, exit_code
  - Metadata: metadata (JSON), context_snapshot (JSON)
- [ ] Foreign key to stories table with CASCADE delete
- [ ] Indexes on workflow_name, status, epic_num, story_num
- [ ] Unit tests for workflow execution tracking

### State Change History Table
- [ ] `state_changes` table for audit trail:
  - Fields: id, table_name, record_id, field_name, old_value, new_value, changed_by, changed_at, reason
  - Index on (table_name, record_id) for fast lookups
- [ ] Triggers on epics/stories/sprints to log state changes
- [ ] Unit tests for audit trail

### Indexes for Performance
- [ ] Stories indexes:
  - idx_stories_status ON stories(status)
  - idx_stories_epic ON stories(epic_num)
  - idx_stories_priority ON stories(priority)
  - idx_stories_owner ON stories(owner)
  - idx_stories_epic_status ON stories(epic_num, status) (composite)
- [ ] Epics indexes:
  - idx_epics_status ON epics(status)
  - idx_epics_feature ON epics(feature)
- [ ] Sprints indexes:
  - idx_sprints_status ON sprints(status)
  - idx_sprints_dates ON sprints(start_date, end_date)
- [ ] Workflow executions indexes:
  - idx_workflow_story ON workflow_executions(epic_num, story_num)
  - idx_workflow_status ON workflow_executions(status)
- [ ] All indexes verified with EXPLAIN QUERY PLAN
- [ ] Unit tests verify indexes created successfully

### Data Integrity
- [ ] Foreign key constraints enforced (PRAGMA foreign_keys = ON)
- [ ] Referential integrity maintained with CASCADE operations
- [ ] CHECK constraints prevent invalid data
- [ ] UNIQUE constraints prevent duplicates
- [ ] NOT NULL constraints on required fields
- [ ] Unit tests for all constraint violations

### Performance
- [ ] Schema creation completes in <100ms
- [ ] All triggers created successfully
- [ ] All indexes created successfully
- [ ] Sample queries tested with EXPLAIN QUERY PLAN
- [ ] Performance baseline established for future comparison

---

## Technical Notes

### Complete Database Schema

```sql
-- Epics table
CREATE TABLE epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_num INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    feature TEXT,
    goal TEXT,
    description TEXT,
    status TEXT NOT NULL CHECK(status IN ('planned', 'active', 'completed', 'cancelled')) DEFAULT 'planned',

    -- Points tracking
    total_points INTEGER DEFAULT 0,
    completed_points INTEGER DEFAULT 0,

    -- Ownership
    owner TEXT,
    created_by TEXT,

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- File sync
    file_path TEXT,
    content_hash TEXT,  -- SHA256 for conflict detection

    -- Extensible metadata
    metadata JSON
);

-- Stories table
CREATE TABLE stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_num INTEGER NOT NULL REFERENCES epics(epic_num) ON UPDATE CASCADE ON DELETE CASCADE,
    story_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,

    -- Status and priority
    status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'done', 'blocked', 'cancelled')) DEFAULT 'pending',
    priority TEXT CHECK(priority IN ('P0', 'P1', 'P2', 'P3')) DEFAULT 'P1',

    -- Story points
    points INTEGER DEFAULT 0,

    -- Ownership
    owner TEXT,
    created_by TEXT,

    -- Timestamps
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    due_date TEXT,

    -- File sync
    file_path TEXT,
    content_hash TEXT,

    -- Extensible metadata
    metadata JSON,
    tags JSON,  -- JSON array of tag strings

    -- Unique constraint
    UNIQUE(epic_num, story_num)
);

-- Sprints table
CREATE TABLE sprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sprint_num INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    goal TEXT,

    -- Status
    status TEXT NOT NULL CHECK(status IN ('planned', 'active', 'completed', 'cancelled')) DEFAULT 'planned',

    -- Dates
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Metrics
    planned_points INTEGER DEFAULT 0,
    completed_points INTEGER DEFAULT 0,
    velocity REAL DEFAULT 0.0,  -- Calculated: completed_points / planned duration

    -- Extensible metadata
    metadata JSON,

    -- Date validation
    CHECK(end_date > start_date)
);

-- Story assignments (many-to-many: stories ↔ sprints)
CREATE TABLE story_assignments (
    sprint_num INTEGER NOT NULL REFERENCES sprints(sprint_num) ON DELETE CASCADE,
    epic_num INTEGER NOT NULL,
    story_num INTEGER NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),

    PRIMARY KEY (sprint_num, epic_num, story_num),
    FOREIGN KEY (epic_num, story_num) REFERENCES stories(epic_num, story_num) ON DELETE CASCADE
);

-- Workflow executions
CREATE TABLE workflow_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_name TEXT NOT NULL,
    phase TEXT,  -- analysis, planning, implementation, etc.

    -- Story linkage
    epic_num INTEGER,
    story_num INTEGER,

    -- Execution details
    status TEXT NOT NULL CHECK(status IN ('started', 'running', 'completed', 'failed', 'cancelled')) DEFAULT 'started',
    executor TEXT NOT NULL,  -- Agent name (John, Amelia, etc.)

    -- Timing
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    duration_ms INTEGER,

    -- Results
    output TEXT,
    error_message TEXT,
    exit_code INTEGER,

    -- Extensible metadata
    metadata JSON,
    context_snapshot JSON,  -- Snapshot of WorkflowContext at execution

    FOREIGN KEY (epic_num, story_num) REFERENCES stories(epic_num, story_num) ON DELETE CASCADE
);

-- State change history (audit trail)
CREATE TABLE state_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,  -- Agent or user
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    reason TEXT,  -- Optional reason for change

    INDEX idx_changes_record (table_name, record_id)
);

-- Indexes for performance
CREATE INDEX idx_stories_status ON stories(status);
CREATE INDEX idx_stories_epic ON stories(epic_num);
CREATE INDEX idx_stories_priority ON stories(priority);
CREATE INDEX idx_stories_owner ON stories(owner);
CREATE INDEX idx_stories_epic_status ON stories(epic_num, status);  -- Composite for common query

CREATE INDEX idx_epics_status ON epics(status);
CREATE INDEX idx_epics_feature ON epics(feature);

CREATE INDEX idx_sprints_status ON sprints(status);
CREATE INDEX idx_sprints_dates ON sprints(start_date, end_date);

CREATE INDEX idx_assignments_sprint ON story_assignments(sprint_num);
CREATE INDEX idx_assignments_story ON story_assignments(epic_num, story_num);

CREATE INDEX idx_workflow_story ON workflow_executions(epic_num, story_num);
CREATE INDEX idx_workflow_status ON workflow_executions(status);
CREATE INDEX idx_workflow_name ON workflow_executions(workflow_name);

-- Triggers for auto-updating timestamps
CREATE TRIGGER update_epic_timestamp
AFTER UPDATE ON epics
FOR EACH ROW
BEGIN
    UPDATE epics SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_story_timestamp
AFTER UPDATE ON stories
FOR EACH ROW
BEGIN
    UPDATE stories SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER update_sprint_timestamp
AFTER UPDATE ON sprints
FOR EACH ROW
BEGIN
    UPDATE sprints SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger for updating epic completed_points when story status changes
CREATE TRIGGER update_epic_points_on_story_status
AFTER UPDATE OF status ON stories
FOR EACH ROW
WHEN NEW.status = 'done' AND OLD.status != 'done'
BEGIN
    UPDATE epics
    SET completed_points = (
        SELECT COALESCE(SUM(points), 0)
        FROM stories
        WHERE epic_num = NEW.epic_num AND status = 'done'
    )
    WHERE epic_num = NEW.epic_num;
END;

-- Trigger for logging state changes (audit trail)
CREATE TRIGGER log_story_status_change
AFTER UPDATE OF status ON stories
FOR EACH ROW
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO state_changes (table_name, record_id, field_name, old_value, new_value, changed_by)
    VALUES ('stories', NEW.id, 'status', OLD.status, NEW.status, 'system');
END;

CREATE TRIGGER log_epic_status_change
AFTER UPDATE OF status ON epics
FOR EACH ROW
WHEN NEW.status != OLD.status
BEGIN
    INSERT INTO state_changes (table_name, record_id, field_name, old_value, new_value, changed_by)
    VALUES ('epics', NEW.id, 'status', OLD.status, NEW.status, 'system');
END;
```

### Schema Migration System

```python
# gao_dev/core/state/migrations/001_create_state_schema.py
import sqlite3
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger()

class Migration001:
    """Create initial state database schema."""

    version = 1
    description = "Create epics, stories, sprints, workflow_executions, state_changes tables"

    @staticmethod
    def upgrade(db_path: Path) -> bool:
        """
        Apply migration to create schema.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(db_path) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Read schema SQL
                schema_sql = (Path(__file__).parent.parent / "schema.sql").read_text()

                # Execute schema creation
                conn.executescript(schema_sql)

                # Create schema_version table if not exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                        description TEXT
                    )
                """)

                # Record migration
                conn.execute("""
                    INSERT INTO schema_version (version, description)
                    VALUES (?, ?)
                """, (Migration001.version, Migration001.description))

                conn.commit()

                logger.info(
                    "migration_applied",
                    version=Migration001.version,
                    description=Migration001.description
                )

                return True

        except Exception as e:
            logger.error("migration_failed", version=Migration001.version, error=str(e))
            return False

    @staticmethod
    def downgrade(db_path: Path) -> bool:
        """
        Rollback migration.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(db_path) as conn:
                # Drop all tables
                tables = ['state_changes', 'workflow_executions', 'story_assignments',
                         'stories', 'sprints', 'epics']
                for table in tables:
                    conn.execute(f"DROP TABLE IF EXISTS {table}")

                # Remove from version table
                conn.execute("DELETE FROM schema_version WHERE version = ?",
                           (Migration001.version,))

                conn.commit()

                logger.info("migration_rolled_back", version=Migration001.version)
                return True

        except Exception as e:
            logger.error("rollback_failed", version=Migration001.version, error=str(e))
            return False
```

### Schema Validation

```python
# gao_dev/core/state/schema_validator.py
import sqlite3
from pathlib import Path
from typing import Dict, List
import structlog

logger = structlog.get_logger()

class SchemaValidator:
    """Validates database schema matches expected structure."""

    EXPECTED_TABLES = {
        'epics', 'stories', 'sprints', 'story_assignments',
        'workflow_executions', 'state_changes', 'schema_version'
    }

    EXPECTED_INDEXES = {
        'idx_stories_status', 'idx_stories_epic', 'idx_stories_priority',
        'idx_stories_owner', 'idx_stories_epic_status',
        'idx_epics_status', 'idx_epics_feature',
        'idx_sprints_status', 'idx_sprints_dates',
        'idx_assignments_sprint', 'idx_assignments_story',
        'idx_workflow_story', 'idx_workflow_status', 'idx_workflow_name'
    }

    @staticmethod
    def validate_schema(db_path: Path) -> Dict[str, bool]:
        """
        Validate database schema.

        Args:
            db_path: Path to database

        Returns:
            Dict with validation results
        """
        results = {
            'tables_valid': False,
            'indexes_valid': False,
            'foreign_keys_enabled': False,
            'triggers_valid': False,
            'errors': []
        }

        try:
            with sqlite3.connect(db_path) as conn:
                # Check foreign keys enabled
                cursor = conn.execute("PRAGMA foreign_keys")
                results['foreign_keys_enabled'] = cursor.fetchone()[0] == 1

                # Check tables exist
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table'
                """)
                tables = {row[0] for row in cursor.fetchall()}
                missing_tables = SchemaValidator.EXPECTED_TABLES - tables

                if missing_tables:
                    results['errors'].append(f"Missing tables: {missing_tables}")
                else:
                    results['tables_valid'] = True

                # Check indexes exist
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """)
                indexes = {row[0] for row in cursor.fetchall()}
                missing_indexes = SchemaValidator.EXPECTED_INDEXES - indexes

                if missing_indexes:
                    results['errors'].append(f"Missing indexes: {missing_indexes}")
                else:
                    results['indexes_valid'] = True

                # Check triggers exist
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM sqlite_master
                    WHERE type='trigger'
                """)
                trigger_count = cursor.fetchone()[0]

                if trigger_count < 5:  # We expect at least 5 triggers
                    results['errors'].append(f"Expected at least 5 triggers, found {trigger_count}")
                else:
                    results['triggers_valid'] = True

        except Exception as e:
            results['errors'].append(f"Validation error: {str(e)}")

        return results
```

**Files to Create:**
- `gao_dev/core/state/__init__.py`
- `gao_dev/core/state/schema.sql` (complete schema)
- `gao_dev/core/state/migrations/__init__.py`
- `gao_dev/core/state/migrations/001_create_state_schema.py`
- `gao_dev/core/state/schema_validator.py`
- `tests/core/state/test_schema_creation.py`
- `tests/core/state/test_schema_validation.py`
- `tests/core/state/test_migrations.py`
- `tests/core/state/test_triggers.py`
- `tests/core/state/test_constraints.py`

**Dependencies:**
- None (foundational story)

---

## Testing Requirements

### Unit Tests

**Schema Creation Tests:**
- [ ] Test all tables created successfully
- [ ] Test all columns exist with correct types
- [ ] Test all constraints created (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK, NOT NULL)
- [ ] Test all indexes created successfully
- [ ] Test all triggers created successfully
- [ ] Test schema creation completes in <100ms

**Constraint Tests:**
- [ ] Test UNIQUE constraint on epics.epic_num prevents duplicates
- [ ] Test UNIQUE constraint on (epic_num, story_num) prevents duplicates
- [ ] Test CHECK constraint on status values rejects invalid values
- [ ] Test CHECK constraint on priority values rejects invalid values
- [ ] Test CHECK constraint on sprint dates (end > start) rejects invalid dates
- [ ] Test NOT NULL constraints reject null values
- [ ] Test DEFAULT values applied correctly

**Foreign Key Tests:**
- [ ] Test CASCADE UPDATE on epic_num propagates to stories
- [ ] Test CASCADE DELETE on epic removes associated stories
- [ ] Test CASCADE DELETE on sprint removes story_assignments
- [ ] Test foreign key violations rejected
- [ ] Test PRAGMA foreign_keys = ON enforced

**Trigger Tests:**
- [ ] Test updated_at timestamp auto-updated on UPDATE
- [ ] Test epic.completed_points auto-calculated when story status changes to 'done'
- [ ] Test state_changes audit log records status changes
- [ ] Test triggers don't fire on INSERT (only UPDATE where applicable)
- [ ] Test trigger performance overhead <5ms

**Index Tests:**
- [ ] Test all indexes created with correct columns
- [ ] Test indexes used in queries (EXPLAIN QUERY PLAN)
- [ ] Test composite indexes work for partial matches
- [ ] Test index performance improves query speed

**Migration Tests:**
- [ ] Test migration applies successfully on fresh database
- [ ] Test migration idempotent (can run multiple times safely)
- [ ] Test migration rollback works correctly
- [ ] Test schema_version table tracks migrations

### Integration Tests
- [ ] Create epic, stories, sprint, assignments in single transaction
- [ ] Test complete workflow: create → update → query → delete
- [ ] Test concurrent insertions don't violate constraints
- [ ] Test large dataset (1000 stories) with acceptable performance

### Performance Tests
- [ ] Schema creation completes in <100ms
- [ ] Insert 1000 stories in <1 second
- [ ] Query by status with index <10ms
- [ ] Update story status with triggers <20ms
- [ ] Complex join query (epic + stories + sprints) <50ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Database schema documentation with ERD diagram
- [ ] Schema migration guide
- [ ] All table and column descriptions documented
- [ ] Index strategy documented
- [ ] Trigger behavior documented
- [ ] Performance benchmarks documented
- [ ] Example queries for common operations

---

## Implementation Details

### Development Approach

1. **Phase 1: Core Schema** (Day 1)
   - Write schema.sql with all tables
   - Create migration script
   - Write schema creation tests

2. **Phase 2: Constraints & Indexes** (Day 2)
   - Add all constraints (UNIQUE, CHECK, NOT NULL, FK)
   - Create all indexes
   - Write constraint and index tests

3. **Phase 3: Triggers** (Day 2)
   - Create auto-update triggers
   - Create audit trail triggers
   - Write trigger tests

4. **Phase 4: Validation & Documentation** (Day 3)
   - Create schema validator
   - Write comprehensive tests
   - Generate ERD diagram
   - Document all components

### Quality Gates
- All tests passing before moving to next phase
- Schema validated with SchemaValidator
- Performance benchmarks met
- ERD diagram reviewed and approved

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete with ERD
- [ ] No regression in existing functionality
- [ ] Performance benchmarks met
- [ ] Schema migration tested on fresh database
- [ ] Schema validator confirms all components present
- [ ] Committed with atomic commit message:
  ```
  feat(epic-15): implement Story 15.1 - State Database Schema

  - Create comprehensive SQLite schema for epics, stories, sprints
  - Add workflow_executions and state_changes tables for tracking
  - Implement triggers for auto-updates and audit trail
  - Create indexes for <50ms query performance
  - Add migration system with rollback capability
  - Create schema validator for integrity checks
  - Add comprehensive unit tests (>80% coverage)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
