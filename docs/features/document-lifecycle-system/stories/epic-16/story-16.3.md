# Story 16.3 (ENHANCED): Context Persistence to Database

**Epic:** 16 - Context Persistence Layer
**Story Points:** 5
**Priority:** P1
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement comprehensive ContextPersistence layer that saves and loads WorkflowContext to/from SQLite database. This enables context to persist across workflow executions, provides complete audit trail of workflow state, supports context versioning for debugging, and enables workflow resumption after interruptions. The persistence layer uses JSON serialization for complex fields and optimizes for fast reads/writes.

---

## Business Value

This story delivers critical capabilities for workflow reliability and debugging:

- **Workflow Continuity**: Resume interrupted workflows from saved context
- **Audit Trail**: Complete history of workflow execution for debugging
- **Debugging**: Inspect context state at any point in workflow execution
- **Rollback**: Restore previous context version if workflow fails
- **Analytics**: Query workflow patterns, decisions, and outcomes
- **Compliance**: Maintain records of all workflow decisions and artifacts
- **Performance**: Fast context loading enables responsive workflow resumption
- **Scalability**: Database storage handles thousands of workflow executions
- **Reliability**: Durable storage prevents context loss on crashes
- **Testing**: Replay workflows from saved context for regression testing

---

## Acceptance Criteria

### Database Schema
- [ ] `workflow_context` table created with all fields
- [ ] Fields: id, workflow_id (unique), epic_num, story_num, feature, workflow_name
- [ ] Fields: current_phase, status, context_data (JSON blob)
- [ ] Fields: created_at, updated_at, version (auto-increment)
- [ ] Index on workflow_id for fast lookups
- [ ] Index on (epic_num, story_num) for story-specific queries
- [ ] Index on status for filtering active workflows
- [ ] Index on created_at for time-based queries
- [ ] JSON context_data field stores serialized WorkflowContext

### Persistence Operations
- [ ] `save_context(context)` serializes and saves to database
- [ ] `load_context(workflow_id)` deserializes and returns WorkflowContext
- [ ] `get_latest_context(epic, story)` returns most recent context for story
- [ ] `get_latest_context_by_status(epic, story, status)` filters by status
- [ ] `delete_context(workflow_id)` removes context
- [ ] `update_context(context)` updates existing context
- [ ] `context_exists(workflow_id)` checks if context exists
- [ ] JSON serialization for complex fields (decisions, artifacts, phase_history)
- [ ] Handles None/null values correctly

### Context Versioning
- [ ] Each save creates new version (auto-increment version field)
- [ ] Version history queryable
- [ ] `get_context_versions(epic, story)` returns all versions ordered by version
- [ ] `get_context_by_version(workflow_id, version)` retrieves specific version
- [ ] `get_version_count(epic, story)` returns total version count
- [ ] Versions immutable (no updates, only inserts)

### Batch Operations
- [ ] `save_contexts(contexts)` batch save multiple contexts
- [ ] `load_contexts(workflow_ids)` batch load multiple contexts
- [ ] Transaction support for batch operations
- [ ] Rollback on batch operation failure

### Query Operations
- [ ] `get_contexts_by_epic(epic_num)` returns all contexts for epic
- [ ] `get_contexts_by_feature(feature)` returns all contexts for feature
- [ ] `get_active_contexts()` returns all running workflows
- [ ] `get_failed_contexts()` returns all failed workflows
- [ ] `search_contexts(filters)` generic search with multiple filters
- [ ] Pagination support for large result sets

### Performance
- [ ] Save operation completes in <50ms
- [ ] Load operation completes in <50ms
- [ ] Batch save 10 contexts in <100ms
- [ ] Query with index completes in <50ms
- [ ] JSON serialization overhead <10ms

---

## Technical Notes

### Database Schema

```sql
-- gao_dev/core/context/migrations/001_create_context_table.sql

CREATE TABLE workflow_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT UNIQUE NOT NULL,
    epic_num INTEGER NOT NULL,
    story_num INTEGER,
    feature TEXT NOT NULL,
    workflow_name TEXT NOT NULL,
    current_phase TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'paused')),
    context_data TEXT NOT NULL,  -- JSON blob
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes for fast lookups
CREATE INDEX idx_workflow_context_workflow_id ON workflow_context(workflow_id);
CREATE INDEX idx_workflow_context_epic_story ON workflow_context(epic_num, story_num);
CREATE INDEX idx_workflow_context_status ON workflow_context(status);
CREATE INDEX idx_workflow_context_created_at ON workflow_context(created_at);
CREATE INDEX idx_workflow_context_feature ON workflow_context(feature);
```

### ContextPersistence Implementation

```python
# gao_dev/core/context/context_persistence.py
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .workflow_context import WorkflowContext
from .exceptions import PersistenceError, ContextNotFoundError

class ContextPersistence:
    """
    Persistence layer for WorkflowContext with SQLite storage.

    Provides save/load operations with versioning, querying, and
    batch operations. Optimized for fast reads/writes.

    Example:
        persistence = ContextPersistence(db_path=Path("gao_dev.db"))

        # Save context
        persistence.save_context(context)

        # Load context
        context = persistence.load_context(workflow_id)

        # Get latest for story
        latest = persistence.get_latest_context(epic=12, story=3)

        # Query contexts
        active = persistence.get_active_contexts()
    """

    def __init__(self, db_path: Path):
        """
        Initialize ContextPersistence.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._ensure_schema_exists()

    def _ensure_schema_exists(self):
        """Ensure workflow_context table exists."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT UNIQUE NOT NULL,
                    epic_num INTEGER NOT NULL,
                    story_num INTEGER,
                    feature TEXT NOT NULL,
                    workflow_name TEXT NOT NULL,
                    current_phase TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'paused')),
                    context_data TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create indexes if not exist
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_context_workflow_id ON workflow_context(workflow_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_context_epic_story ON workflow_context(epic_num, story_num)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_context_status ON workflow_context(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_context_created_at ON workflow_context(created_at)")

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise PersistenceError(f"Database error: {e}") from e
        finally:
            conn.close()

    def save_context(self, context: WorkflowContext) -> int:
        """
        Save context to database.

        Args:
            context: WorkflowContext to save

        Returns:
            Version number of saved context

        Raises:
            PersistenceError: If save fails
        """
        with self._get_connection() as conn:
            # Serialize context to JSON
            context_json = context.to_json()

            # Check if context already exists
            cursor = conn.execute(
                "SELECT version FROM workflow_context WHERE workflow_id = ?",
                (context.workflow_id,)
            )
            row = cursor.fetchone()

            if row:
                # Update existing context (increment version)
                version = row['version'] + 1
                conn.execute(
                    """
                    UPDATE workflow_context
                    SET epic_num = ?, story_num = ?, feature = ?, workflow_name = ?,
                        current_phase = ?, status = ?, context_data = ?, version = ?,
                        updated_at = ?
                    WHERE workflow_id = ?
                    """,
                    (context.epic_num, context.story_num, context.feature, context.workflow_name,
                     context.current_phase, context.status, context_json, version,
                     datetime.now().isoformat(), context.workflow_id)
                )
            else:
                # Insert new context
                version = 1
                conn.execute(
                    """
                    INSERT INTO workflow_context
                    (workflow_id, epic_num, story_num, feature, workflow_name, current_phase,
                     status, context_data, version, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (context.workflow_id, context.epic_num, context.story_num, context.feature,
                     context.workflow_name, context.current_phase, context.status, context_json,
                     version, context.created_at, context.updated_at)
                )

            return version

    def load_context(self, workflow_id: str) -> WorkflowContext:
        """
        Load context from database.

        Args:
            workflow_id: Workflow execution ID

        Returns:
            WorkflowContext instance

        Raises:
            ContextNotFoundError: If context not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT context_data FROM workflow_context WHERE workflow_id = ?",
                (workflow_id,)
            )
            row = cursor.fetchone()

            if not row:
                raise ContextNotFoundError(f"Context not found: {workflow_id}")

            # Deserialize from JSON
            context_json = row['context_data']
            return WorkflowContext.from_json(context_json)

    def get_latest_context(self, epic_num: int, story_num: Optional[int] = None) -> Optional[WorkflowContext]:
        """
        Get most recent context for story.

        Args:
            epic_num: Epic number
            story_num: Story number (optional)

        Returns:
            Latest WorkflowContext or None if not found
        """
        with self._get_connection() as conn:
            if story_num is not None:
                cursor = conn.execute(
                    """
                    SELECT context_data FROM workflow_context
                    WHERE epic_num = ? AND story_num = ?
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (epic_num, story_num)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT context_data FROM workflow_context
                    WHERE epic_num = ? AND story_num IS NULL
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (epic_num,)
                )

            row = cursor.fetchone()
            if not row:
                return None

            context_json = row['context_data']
            return WorkflowContext.from_json(context_json)

    def delete_context(self, workflow_id: str) -> bool:
        """
        Delete context from database.

        Args:
            workflow_id: Workflow execution ID

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM workflow_context WHERE workflow_id = ?",
                (workflow_id,)
            )
            return cursor.rowcount > 0

    def context_exists(self, workflow_id: str) -> bool:
        """
        Check if context exists.

        Args:
            workflow_id: Workflow execution ID

        Returns:
            True if exists, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM workflow_context WHERE workflow_id = ? LIMIT 1",
                (workflow_id,)
            )
            return cursor.fetchone() is not None

    def get_context_versions(self, epic_num: int, story_num: Optional[int] = None) -> List[WorkflowContext]:
        """
        Get all context versions for story.

        Args:
            epic_num: Epic number
            story_num: Story number (optional)

        Returns:
            List of WorkflowContext instances ordered by version
        """
        with self._get_connection() as conn:
            if story_num is not None:
                cursor = conn.execute(
                    """
                    SELECT context_data FROM workflow_context
                    WHERE epic_num = ? AND story_num = ?
                    ORDER BY version ASC
                    """,
                    (epic_num, story_num)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT context_data FROM workflow_context
                    WHERE epic_num = ? AND story_num IS NULL
                    ORDER BY version ASC
                    """,
                    (epic_num,)
                )

            contexts = []
            for row in cursor.fetchall():
                context_json = row['context_data']
                contexts.append(WorkflowContext.from_json(context_json))

            return contexts

    def get_active_contexts(self) -> List[WorkflowContext]:
        """
        Get all active (running) workflow contexts.

        Returns:
            List of WorkflowContext instances
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT context_data FROM workflow_context WHERE status = 'running' ORDER BY created_at DESC"
            )

            contexts = []
            for row in cursor.fetchall():
                context_json = row['context_data']
                contexts.append(WorkflowContext.from_json(context_json))

            return contexts

    def save_contexts(self, contexts: List[WorkflowContext]) -> List[int]:
        """
        Batch save multiple contexts.

        Args:
            contexts: List of WorkflowContext instances

        Returns:
            List of version numbers

        Raises:
            PersistenceError: If batch save fails
        """
        versions = []
        with self._get_connection() as conn:
            for context in contexts:
                version = self.save_context(context)
                versions.append(version)
        return versions

    def get_contexts_by_feature(self, feature: str) -> List[WorkflowContext]:
        """
        Get all contexts for feature.

        Args:
            feature: Feature name

        Returns:
            List of WorkflowContext instances
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT context_data FROM workflow_context WHERE feature = ? ORDER BY created_at DESC",
                (feature,)
            )

            contexts = []
            for row in cursor.fetchall():
                context_json = row['context_data']
                contexts.append(WorkflowContext.from_json(context_json))

            return contexts
```

**Files to Create:**
- `gao_dev/core/context/context_persistence.py`
- `gao_dev/core/context/migrations/001_create_context_table.sql`
- `gao_dev/core/context/exceptions.py` (add PersistenceError, ContextNotFoundError)
- `tests/core/context/test_context_persistence.py`
- `tests/core/context/test_context_persistence_batch.py`

**Dependencies:** Story 16.2 (WorkflowContext), Epic 15 (State Database)

---

## Testing Requirements

### Unit Tests

**Save Operations:**
- [ ] Test `save_context()` creates new context
- [ ] Test `save_context()` updates existing context
- [ ] Test `save_context()` increments version
- [ ] Test `save_context()` serializes complex fields correctly
- [ ] Test `save_contexts()` batch saves multiple contexts
- [ ] Test save handles None/null values correctly

**Load Operations:**
- [ ] Test `load_context()` retrieves context
- [ ] Test `load_context()` raises ContextNotFoundError if not found
- [ ] Test `load_context()` deserializes correctly
- [ ] Test `get_latest_context()` returns most recent
- [ ] Test `get_latest_context()` handles story_num=None
- [ ] Test `get_latest_context()` returns None if not found

**Delete Operations:**
- [ ] Test `delete_context()` removes context
- [ ] Test `delete_context()` returns False if not found
- [ ] Test `context_exists()` checks existence correctly

**Versioning:**
- [ ] Test `get_context_versions()` returns all versions
- [ ] Test versions ordered correctly
- [ ] Test version numbers increment correctly
- [ ] Test version immutability (no updates to old versions)

**Query Operations:**
- [ ] Test `get_active_contexts()` filters by status
- [ ] Test `get_contexts_by_feature()` filters by feature
- [ ] Test queries use indexes (explain query plan)

### Integration Tests
- [ ] Create context, save, load, verify identity
- [ ] Save multiple versions, query versions, verify order
- [ ] Save contexts, query by feature, verify filtering
- [ ] Delete context, verify load fails
- [ ] Round-trip serialization (save -> load -> compare)

### Performance Tests
- [ ] Save operation completes in <50ms
- [ ] Load operation completes in <50ms
- [ ] Batch save 10 contexts in <100ms
- [ ] Query with index completes in <50ms
- [ ] JSON serialization overhead <10ms

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all methods
- [ ] Database schema documentation with ERD
- [ ] Versioning behavior documentation
- [ ] Performance characteristics documentation
- [ ] Query optimization guide
- [ ] Example usage patterns
- [ ] Migration guide for schema changes
- [ ] Troubleshooting guide

---

## Implementation Details

### Development Approach

**Phase 1: Schema & Basic Operations**
1. Create database schema and migrations
2. Implement save_context and load_context
3. Add basic error handling
4. Write unit tests for save/load

**Phase 2: Versioning & Queries**
1. Implement versioning logic
2. Add query operations (get_latest, get_versions)
3. Add filtering queries (by feature, status)
4. Write query tests

**Phase 3: Batch & Optimization**
1. Implement batch operations
2. Add transaction support
3. Optimize queries with indexes
4. Add performance tests

### Quality Gates
- [ ] All unit tests pass with >80% coverage
- [ ] Performance benchmarks met (<50ms operations)
- [ ] Schema migration tested
- [ ] Round-trip serialization verified
- [ ] Documentation complete with examples

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] Database schema created with indexes
- [ ] Save/load operations working correctly
- [ ] Context versioning implemented
- [ ] Query operations implemented
- [ ] Batch operations supported
- [ ] JSON serialization working correctly
- [ ] Tests passing (>80% coverage)
- [ ] Performance benchmarks met (<50ms operations)
- [ ] Code reviewed and approved
- [ ] Documentation complete with examples
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-16): implement Story 16.3 - Context Persistence to Database

  - Create workflow_context table with versioning support
  - Implement save_context and load_context operations
  - Add context versioning (auto-increment version field)
  - Implement query operations (get_latest, get_versions, by_feature, by_status)
  - Support batch operations with transactions
  - Add comprehensive indexes for fast lookups
  - Implement JSON serialization for complex fields
  - Add comprehensive unit tests (>80% coverage)
  - Performance optimizations (<50ms operations)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
