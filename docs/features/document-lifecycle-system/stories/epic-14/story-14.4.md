# Story 14.4: Checklist Execution Tracking

**Epic:** 14 - Checklist Plugin System
**Story Points:** 5 | **Priority:** P1 | **Status:** Pending | **Owner:** TBD | **Sprint:** TBD

---

## Story Description

Track checklist executions in database with pass/fail results per item. Enable compliance reporting and audit trails by recording who executed checklists, when, and what the results were. This story provides the foundation for quality gates, compliance auditing, and continuous improvement of development practices.

---

## Business Value

This story enables the quality gate system that ensures production-ready deliverables:

- **Compliance Auditing**: Full audit trail of all quality checks performed
- **Quality Gates**: Block story completion until required checklists pass
- **Continuous Improvement**: Identify frequently failing checklist items for process improvement
- **Accountability**: Track who executed checklists and when
- **Trend Analysis**: Measure checklist pass rates over time to improve practices
- **Partial Completion**: Support for incremental checklist execution (some items NA/skip)

---

## Acceptance Criteria

### Database Schema
- [ ] `checklist_executions` table created with all required fields:
  - Core: execution_id, checklist_name, checklist_version, artifact_type, artifact_id
  - Tracking: executed_by, executed_at, overall_status, duration_ms
  - Linkage: epic_num, story_num, workflow_execution_id
  - Metadata: notes, metadata (JSON)
- [ ] `checklist_results` table for item-level results:
  - Fields: execution_id, item_id, status, notes, timestamp
  - Foreign key to checklist_executions with CASCADE delete
- [ ] Indexes created on frequently queried columns:
  - checklist_name, artifact_id, epic_num, story_num, overall_status, executed_at
- [ ] Foreign key constraints enforced to stories/artifacts
- [ ] CHECK constraints for status values
- [ ] Unit tests for schema creation and validation

### Tracking API
- [ ] `track_execution()` records checklist execution start
  - Returns execution_id for recording item results
  - Records checklist metadata (name, version, artifact)
  - Initializes overall_status as 'in_progress'
- [ ] `record_item_result()` records individual item results
  - Validates item_id exists in checklist definition
  - Validates status value (pass, fail, skip, na)
  - Allows optional notes per item
  - Updates execution timestamp
- [ ] `complete_execution()` finalizes execution
  - Calculates overall_status from item results
  - Records total duration
  - Validates all required items have results
- [ ] Overall status calculation logic:
  - pass: All required items pass (skip/na ignored)
  - fail: Any required item fails
  - partial: Some required items pass, some skip/na
  - in_progress: Not yet completed
- [ ] Thread-safe operations with database transactions
- [ ] Unit tests for all tracking methods (>80% coverage)

### Query Interface
- [ ] `get_execution_results(execution_id)` - Returns complete execution with item results
  - Joins executions and results tables
  - Returns ExecutionResult dataclass
  - Includes checklist definition for context
- [ ] `get_story_checklists(epic, story)` - Returns all checklist executions for story
  - Sorted by execution time (most recent first)
  - Includes overall status for quick filtering
- [ ] `get_failed_items(execution_id)` - Returns only failed items with notes
  - Useful for quality gate reporting
  - Includes item text and help_text from definition
- [ ] `get_checklist_history(checklist_name)` - Returns all executions of specific checklist
  - Aggregate statistics: total executions, pass rate, avg duration
  - Identifies most frequently failing items
- [ ] `get_compliance_report(artifact_type, date_range)` - Aggregate compliance metrics
  - Pass rate by checklist type
  - Trend analysis over time
  - Identify quality bottlenecks
- [ ] `get_pending_checklists(epic, story)` - Returns required checklists not yet executed
  - Based on story type and phase
  - Useful for quality gate enforcement
- [ ] Unit tests for all query methods

### Status Values
- [ ] `pass` - Item passed all criteria
- [ ] `fail` - Item failed one or more criteria
- [ ] `skip` - Item intentionally skipped (documented reason required)
- [ ] `na` - Item not applicable to this artifact
- [ ] Overall execution statuses:
  - `in_progress` - Execution started, not completed
  - `pass` - All required items passed
  - `fail` - One or more required items failed
  - `partial` - Mix of pass/skip/na, no failures
- [ ] Status transitions validated
- [ ] Status enum validation in database schema

### Batch Operations
- [ ] `track_batch_execution()` records multiple item results atomically
  - Single database transaction
  - Rollback on any validation error
  - Optimized for bulk checklist execution
- [ ] `import_execution_results()` imports from JSON/YAML
  - Useful for CLI-based checklist execution
  - Validates all data before import
- [ ] Performance: Batch insert 100 items <500ms

### Performance
- [ ] Track execution <50ms
- [ ] Record item result <10ms
- [ ] Query execution results <50ms
- [ ] Batch operations optimized with prepared statements
- [ ] Database connection pooling for concurrent access

---

## Technical Notes

### Database Schema Details

```sql
-- Checklist executions table
CREATE TABLE checklist_executions (
    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_name TEXT NOT NULL,
    checklist_version TEXT NOT NULL,  -- Version of checklist executed
    artifact_type TEXT NOT NULL CHECK(artifact_type IN ('story', 'epic', 'prd', 'architecture', 'code')),
    artifact_id TEXT NOT NULL,  -- Story path, epic number, file path, etc.

    -- Story/Epic linkage
    epic_num INTEGER,
    story_num INTEGER,
    workflow_execution_id INTEGER,  -- Link to workflow that triggered this

    -- Execution metadata
    executed_by TEXT NOT NULL,  -- Agent or user who executed
    executed_at TEXT NOT NULL,  -- ISO timestamp
    completed_at TEXT,  -- ISO timestamp when completed
    duration_ms INTEGER,  -- Total execution time

    -- Status
    overall_status TEXT NOT NULL CHECK(overall_status IN ('in_progress', 'pass', 'fail', 'partial')),

    -- Additional metadata
    notes TEXT,  -- Overall execution notes
    metadata JSON,  -- Extensible metadata (environment, context, etc.)

    FOREIGN KEY (epic_num, story_num) REFERENCES stories(epic_num, story_num) ON DELETE CASCADE
);

-- Checklist item results table
CREATE TABLE checklist_results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id INTEGER NOT NULL REFERENCES checklist_executions(execution_id) ON DELETE CASCADE,

    -- Item identification
    item_id TEXT NOT NULL,  -- Item ID from checklist definition
    item_category TEXT,  -- Category for grouping

    -- Result
    status TEXT NOT NULL CHECK(status IN ('pass', 'fail', 'skip', 'na')),
    notes TEXT,  -- Notes for this specific item (reason for fail/skip)

    -- Tracking
    checked_at TEXT NOT NULL,  -- ISO timestamp
    checked_by TEXT,  -- Could differ from overall executed_by

    -- Evidence (optional)
    evidence_path TEXT,  -- Path to evidence file/screenshot
    evidence_metadata JSON  -- Additional evidence metadata
);

-- Indexes for fast queries
CREATE INDEX idx_executions_checklist ON checklist_executions(checklist_name);
CREATE INDEX idx_executions_artifact ON checklist_executions(artifact_type, artifact_id);
CREATE INDEX idx_executions_story ON checklist_executions(epic_num, story_num);
CREATE INDEX idx_executions_status ON checklist_executions(overall_status);
CREATE INDEX idx_executions_date ON checklist_executions(executed_at);
CREATE INDEX idx_results_execution ON checklist_results(execution_id);
CREATE INDEX idx_results_status ON checklist_results(status);
```

### ChecklistTracker Implementation

```python
# gao_dev/core/checklists/checklist_tracker.py
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json

@dataclass
class ItemResult:
    """Result of a single checklist item."""
    item_id: str
    item_category: str
    status: str  # pass, fail, skip, na
    notes: Optional[str] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[str] = None
    evidence_path: Optional[str] = None

@dataclass
class ExecutionResult:
    """Complete checklist execution result."""
    execution_id: int
    checklist_name: str
    checklist_version: str
    artifact_type: str
    artifact_id: str
    epic_num: Optional[int]
    story_num: Optional[int]
    executed_by: str
    executed_at: datetime
    completed_at: Optional[datetime]
    overall_status: str
    item_results: List[ItemResult]
    notes: Optional[str] = None
    duration_ms: Optional[int] = None

class ChecklistTracker:
    """Tracks checklist execution and results in database."""

    def __init__(self, db_path: Path):
        """Initialize tracker with database path."""
        self.db_path = db_path
        self._ensure_schema()

    def track_execution(
        self,
        checklist_name: str,
        checklist_version: str,
        artifact_type: str,
        artifact_id: str,
        executed_by: str,
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        workflow_execution_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Start tracking a checklist execution.

        Args:
            checklist_name: Name of checklist being executed
            checklist_version: Version of checklist
            artifact_type: Type of artifact (story, epic, prd, etc.)
            artifact_id: ID of artifact
            executed_by: Who is executing (agent or user name)
            epic_num: Epic number if applicable
            story_num: Story number if applicable
            workflow_execution_id: Link to workflow execution
            metadata: Additional metadata

        Returns:
            execution_id for recording item results

        Example:
            execution_id = tracker.track_execution(
                checklist_name="qa-comprehensive",
                checklist_version="1.0",
                artifact_type="story",
                artifact_id="12.1",
                executed_by="Amelia",
                epic_num=12,
                story_num=1
            )
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checklist_executions (
                    checklist_name, checklist_version, artifact_type, artifact_id,
                    epic_num, story_num, workflow_execution_id,
                    executed_by, executed_at, overall_status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_progress', ?)
            """, (
                checklist_name, checklist_version, artifact_type, artifact_id,
                epic_num, story_num, workflow_execution_id,
                executed_by, datetime.now().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            return cursor.lastrowid

    def record_item_result(
        self,
        execution_id: int,
        item_id: str,
        status: str,
        item_category: Optional[str] = None,
        notes: Optional[str] = None,
        checked_by: Optional[str] = None,
        evidence_path: Optional[str] = None
    ):
        """
        Record result for a single checklist item.

        Args:
            execution_id: ID from track_execution()
            item_id: Item ID from checklist definition
            status: pass, fail, skip, or na
            item_category: Category for grouping
            notes: Notes for this item (required for fail/skip)
            checked_by: Who checked this item
            evidence_path: Path to evidence file
        """
        # Validate status
        valid_statuses = {'pass', 'fail', 'skip', 'na'}
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

        # Require notes for fail/skip
        if status in {'fail', 'skip'} and not notes:
            raise ValueError(f"Notes required for status '{status}'")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checklist_results (
                    execution_id, item_id, item_category, status, notes,
                    checked_at, checked_by, evidence_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                execution_id, item_id, item_category, status, notes,
                datetime.now().isoformat(), checked_by, evidence_path
            ))

    def complete_execution(
        self,
        execution_id: int,
        notes: Optional[str] = None
    ) -> str:
        """
        Complete checklist execution and calculate overall status.

        Args:
            execution_id: ID from track_execution()
            notes: Overall execution notes

        Returns:
            overall_status (pass, fail, partial)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get all item results
            cursor.execute("""
                SELECT status FROM checklist_results
                WHERE execution_id = ?
            """, (execution_id,))
            statuses = [row[0] for row in cursor.fetchall()]

            # Calculate overall status
            if 'fail' in statuses:
                overall_status = 'fail'
            elif all(s in {'pass', 'skip', 'na'} for s in statuses):
                if 'pass' in statuses:
                    overall_status = 'pass'
                else:
                    overall_status = 'partial'
            else:
                overall_status = 'partial'

            # Get execution start time to calculate duration
            cursor.execute("""
                SELECT executed_at FROM checklist_executions
                WHERE execution_id = ?
            """, (execution_id,))
            executed_at = datetime.fromisoformat(cursor.fetchone()[0])
            duration_ms = int((datetime.now() - executed_at).total_seconds() * 1000)

            # Update execution record
            cursor.execute("""
                UPDATE checklist_executions
                SET overall_status = ?, completed_at = ?, duration_ms = ?, notes = ?
                WHERE execution_id = ?
            """, (overall_status, datetime.now().isoformat(), duration_ms, notes, execution_id))

            return overall_status

    def get_execution_results(self, execution_id: int) -> ExecutionResult:
        """Get complete execution results including all item results."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get execution record
            cursor.execute("""
                SELECT checklist_name, checklist_version, artifact_type, artifact_id,
                       epic_num, story_num, executed_by, executed_at, completed_at,
                       overall_status, notes, duration_ms
                FROM checklist_executions
                WHERE execution_id = ?
            """, (execution_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Execution {execution_id} not found")

            # Get item results
            cursor.execute("""
                SELECT item_id, item_category, status, notes, checked_at,
                       checked_by, evidence_path
                FROM checklist_results
                WHERE execution_id = ?
                ORDER BY checked_at
            """, (execution_id,))

            item_results = [
                ItemResult(
                    item_id=r[0],
                    item_category=r[1],
                    status=r[2],
                    notes=r[3],
                    checked_at=datetime.fromisoformat(r[4]) if r[4] else None,
                    checked_by=r[5],
                    evidence_path=r[6]
                )
                for r in cursor.fetchall()
            ]

            return ExecutionResult(
                execution_id=execution_id,
                checklist_name=row[0],
                checklist_version=row[1],
                artifact_type=row[2],
                artifact_id=row[3],
                epic_num=row[4],
                story_num=row[5],
                executed_by=row[6],
                executed_at=datetime.fromisoformat(row[7]),
                completed_at=datetime.fromisoformat(row[8]) if row[8] else None,
                overall_status=row[9],
                notes=row[10],
                duration_ms=row[11],
                item_results=item_results
            )
```

**Files to Create:**
- `gao_dev/core/checklists/__init__.py`
- `gao_dev/core/checklists/checklist_tracker.py`
- `gao_dev/core/checklists/models.py` (ExecutionResult, ItemResult dataclasses)
- `gao_dev/core/checklists/migrations/001_create_checklist_tables.sql`
- `tests/core/checklists/test_checklist_tracker.py`
- `tests/core/checklists/test_checklist_queries.py`

**Dependencies:**
- Story 14.2 (ChecklistLoader) - For checklist definitions
- Epic 15 (State Database) - For stories table foreign key

---

## Testing Requirements

### Unit Tests

**Schema Tests:**
- [ ] Test tables created successfully
- [ ] Test all indexes created
- [ ] Test foreign key constraints work
- [ ] Test CHECK constraints enforce valid values
- [ ] Test CASCADE delete works correctly

**Tracking Tests:**
- [ ] Test `track_execution()` creates record
- [ ] Test `record_item_result()` validates status
- [ ] Test `record_item_result()` requires notes for fail/skip
- [ ] Test `complete_execution()` calculates status correctly
- [ ] Test overall status = 'fail' when any item fails
- [ ] Test overall status = 'pass' when all required items pass
- [ ] Test overall status = 'partial' for skip/na mix
- [ ] Test duration calculation is accurate

**Query Tests:**
- [ ] Test `get_execution_results()` returns complete data
- [ ] Test `get_story_checklists()` filters by story
- [ ] Test `get_failed_items()` returns only failures
- [ ] Test `get_checklist_history()` aggregates correctly
- [ ] Test `get_compliance_report()` generates statistics
- [ ] Test queries use indexes (EXPLAIN QUERY PLAN)

**Batch Operation Tests:**
- [ ] Test batch insert performance
- [ ] Test transaction rollback on error
- [ ] Test import from JSON/YAML

### Integration Tests
- [ ] Execute complete checklist workflow end-to-end
- [ ] Test with real ChecklistLoader integration
- [ ] Test concurrent executions from multiple threads
- [ ] Test database connection pooling

### Performance Tests
- [ ] Track execution completes in <50ms
- [ ] Record item result completes in <10ms
- [ ] Query execution results completes in <50ms
- [ ] Batch insert 100 items in <500ms
- [ ] 1000 executions queryable in <100ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all classes and methods
- [ ] API documentation for ChecklistTracker
- [ ] Database schema documentation with ERD
- [ ] Usage examples for common scenarios
- [ ] Query performance optimization guide
- [ ] Compliance reporting guide

---

## Implementation Details

### Development Approach

1. **Phase 1: Schema & Models** (Day 1)
   - Create database schema SQL
   - Define dataclasses (ExecutionResult, ItemResult)
   - Write schema creation tests

2. **Phase 2: Core Tracking** (Day 2)
   - Implement track_execution()
   - Implement record_item_result()
   - Implement complete_execution()
   - Write unit tests for tracking

3. **Phase 3: Query Interface** (Day 3)
   - Implement all query methods
   - Optimize with indexes
   - Write query tests

4. **Phase 4: Batch Operations & Polish** (Day 4)
   - Implement batch operations
   - Performance testing and optimization
   - Integration tests

### Quality Gates
- All unit tests passing before moving to next phase
- Performance benchmarks met before integration
- Code review by senior developer
- Documentation complete and reviewed

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All tests passing (>80% coverage)
- [ ] Code reviewed and approved
- [ ] Documentation complete
- [ ] No regression in existing functionality
- [ ] Performance benchmarks met
- [ ] Integration tests with ChecklistLoader passing
- [ ] Committed with atomic commit message:
  ```
  feat(epic-14): implement Story 14.4 - Checklist Execution Tracking

  - Create checklist_executions and checklist_results tables
  - Implement ChecklistTracker with tracking and query APIs
  - Add overall status calculation logic (pass/fail/partial)
  - Support batch operations for performance
  - Add comprehensive query interface for compliance reporting
  - Add unit tests (>80% coverage) and performance tests

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
