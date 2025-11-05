# Story 15.2 (ENHANCED): StateTracker Implementation

**Epic:** 15 - State Tracking Database
**Story Points:** 6
**Priority:** P0
**Status:** Pending
**Owner:** TBD
**Sprint:** TBD

---

## Story Description

Implement StateTracker class with comprehensive CRUD operations for stories, epics, sprints, and workflows. This provides the Python API for all state management operations with thread-safe access, transaction support, and rich query capabilities. StateTracker is the central data access layer for the entire GAO-Dev system, enabling agents to track progress, query state, and maintain consistency across workflow executions.

---

## Business Value

This story delivers the critical data access layer that enables GAO-Dev's autonomous capabilities:

- **Autonomous State Management**: Agents can query and update state without manual intervention
- **Progress Tracking**: Real-time visibility into epic, sprint, and story completion
- **Velocity Calculation**: Sprint velocity metrics enable accurate planning and forecasting
- **Workflow Audit Trail**: Complete history of workflow executions for debugging and optimization
- **Data Integrity**: Thread-safe operations ensure consistency in concurrent agent execution
- **Performance**: Fast queries (<50ms) enable responsive agent interactions
- **Scalability**: Prepared statements and connection pooling support large-scale operations
- **Query Flexibility**: Rich query API supports complex filtering and aggregation
- **Type Safety**: Dataclass returns provide compile-time type checking and IDE support
- **Transaction Support**: Multi-step operations maintain consistency during complex updates

---

## Acceptance Criteria

### Story Operations
- [ ] `create_story()` creates new story record with all required fields
- [ ] `get_story(epic, story_num)` retrieves story by epic and story number
- [ ] `update_story_status(epic, story_num, status)` updates story status with timestamp
- [ ] `update_story_owner(epic, story_num, owner)` assigns owner
- [ ] `update_story_points(epic, story_num, points)` updates story points
- [ ] `get_stories_by_status(status)` queries by status with pagination
- [ ] `get_stories_by_epic(epic_num)` queries by epic with ordering
- [ ] `get_stories_by_sprint(sprint_num)` returns all stories in sprint
- [ ] `get_stories_in_progress()` returns all in-progress stories
- [ ] `get_blocked_stories()` returns stories with blockers
- [ ] Returns Story dataclass instances with all fields populated

### Epic Operations
- [ ] `create_epic(epic_num, title, feature, total_points)` creates new epic
- [ ] `get_epic(epic_num)` retrieves epic with computed fields
- [ ] `get_epic_progress(epic_num)` calculates completion percentage
- [ ] `update_epic_points(epic_num, total, completed)` updates points
- [ ] `update_epic_status(epic_num, status)` updates epic status
- [ ] `get_active_epics()` returns epics with status='active'
- [ ] `get_epics_by_feature(feature)` queries by feature name
- [ ] `get_epic_velocity(epic_num)` calculates average story completion rate
- [ ] Returns Epic dataclass instances with computed progress

### Sprint Operations
- [ ] `create_sprint(sprint_num, start_date, end_date)` creates new sprint
- [ ] `get_sprint(sprint_num)` retrieves sprint with metadata
- [ ] `assign_story_to_sprint(epic, story_num, sprint_num)` assigns story
- [ ] `unassign_story_from_sprint(epic, story_num)` removes assignment
- [ ] `get_sprint_stories(sprint_num)` gets all stories in sprint
- [ ] `get_sprint_velocity(sprint_num)` calculates velocity (points completed)
- [ ] `get_sprint_completion_rate(sprint_num)` calculates story completion rate
- [ ] `get_current_sprint()` returns active sprint
- [ ] `get_sprint_burndown_data(sprint_num)` returns daily progress data
- [ ] Returns Sprint dataclass instances with computed metrics

### Workflow Operations
- [ ] `track_workflow_execution(workflow_id, epic, story, workflow_name)` records workflow run
- [ ] `update_workflow_status(workflow_id, status, result)` updates execution status
- [ ] `get_story_workflow_history(epic, story)` gets execution history ordered by timestamp
- [ ] `get_workflow_execution(workflow_id)` retrieves specific execution
- [ ] `get_failed_workflows()` returns workflows with status='failed'
- [ ] `get_workflow_metrics(workflow_name)` aggregates success rate and duration
- [ ] Returns WorkflowExecution dataclass instances

### Data Integrity
- [ ] Thread-safe operations using connection pooling
- [ ] Transaction support for multi-step operations with rollback
- [ ] Return typed dataclass instances (Story, Epic, Sprint, WorkflowExecution models)
- [ ] Prepared statements for SQL injection prevention
- [ ] Foreign key enforcement for referential integrity
- [ ] Validation of enum values (status, priority)
- [ ] Automatic timestamp updates (created_at, updated_at)
- [ ] Graceful error handling with descriptive exceptions

### Performance
- [ ] All queries complete in <50ms (p99)
- [ ] Batch operations supported (insert multiple stories)
- [ ] Query result caching for frequently accessed data
- [ ] Index usage verified for all queries
- [ ] Connection pooling reduces overhead
- [ ] Pagination supported for large result sets

---

## Technical Notes

### StateTracker Implementation

```python
# gao_dev/core/state/state_tracker.py
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from .models import Story, Epic, Sprint, WorkflowExecution
from .exceptions import StateTrackerError, RecordNotFoundError

class StateTracker:
    """
    Thread-safe state tracker for GAO-Dev with CRUD operations.

    Provides data access layer for stories, epics, sprints, and workflows
    with transaction support and connection pooling.
    """

    def __init__(self, db_path: Path):
        """
        Initialize StateTracker.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        """Ensure database and schema exist."""
        if not self.db_path.exists():
            raise StateTrackerError(f"Database not found: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise StateTrackerError(f"Database error: {e}") from e
        finally:
            conn.close()

    # ==================== STORY OPERATIONS ====================

    def create_story(
        self,
        epic_num: int,
        story_num: int,
        title: str,
        status: str = "pending",
        owner: Optional[str] = None,
        points: int = 0,
        priority: str = "P1",
        sprint: Optional[int] = None
    ) -> Story:
        """
        Create new story.

        Args:
            epic_num: Epic number
            story_num: Story number within epic
            title: Story title
            status: Story status (default: 'pending')
            owner: Story owner
            points: Story points
            priority: Priority (P0-P3)
            sprint: Sprint number (optional)

        Returns:
            Created Story instance
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO stories (epic, story_num, title, status, owner, points, priority, sprint, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (epic_num, story_num, title, status, owner, points, priority, sprint,
                 datetime.now().isoformat(), datetime.now().isoformat())
            )
            return self.get_story(epic_num, story_num)

    def get_story(self, epic_num: int, story_num: int) -> Story:
        """Get story by epic and story number."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stories WHERE epic = ? AND story_num = ?",
                (epic_num, story_num)
            )
            row = cursor.fetchone()
            if not row:
                raise RecordNotFoundError(f"Story {epic_num}.{story_num} not found")
            return Story(**dict(row))

    def update_story_status(self, epic_num: int, story_num: int, status: str) -> Story:
        """Update story status."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE stories SET status = ?, updated_at = ? WHERE epic = ? AND story_num = ?",
                (status, datetime.now().isoformat(), epic_num, story_num)
            )
            return self.get_story(epic_num, story_num)

    def get_stories_by_status(self, status: str, limit: int = 100, offset: int = 0) -> List[Story]:
        """Get stories by status with pagination."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stories WHERE status = ? ORDER BY epic, story_num LIMIT ? OFFSET ?",
                (status, limit, offset)
            )
            return [Story(**dict(row)) for row in cursor.fetchall()]

    def get_stories_by_epic(self, epic_num: int) -> List[Story]:
        """Get all stories in epic."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stories WHERE epic = ? ORDER BY story_num",
                (epic_num,)
            )
            return [Story(**dict(row)) for row in cursor.fetchall()]

    # ==================== EPIC OPERATIONS ====================

    def create_epic(self, epic_num: int, title: str, feature: str, total_points: int = 0) -> Epic:
        """Create new epic."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO epics (epic_num, title, feature, status, total_points, completed_points, created_at, updated_at)
                VALUES (?, ?, ?, 'active', ?, 0, ?, ?)
                """,
                (epic_num, title, feature, total_points, datetime.now().isoformat(), datetime.now().isoformat())
            )
            return self.get_epic(epic_num)

    def get_epic(self, epic_num: int) -> Epic:
        """Get epic with computed progress."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM epics WHERE epic_num = ?", (epic_num,))
            row = cursor.fetchone()
            if not row:
                raise RecordNotFoundError(f"Epic {epic_num} not found")

            epic_data = dict(row)
            # Compute progress percentage
            if epic_data['total_points'] > 0:
                epic_data['progress'] = (epic_data['completed_points'] / epic_data['total_points']) * 100
            else:
                epic_data['progress'] = 0.0

            return Epic(**epic_data)

    def get_epic_progress(self, epic_num: int) -> float:
        """Calculate epic completion percentage."""
        epic = self.get_epic(epic_num)
        return epic.progress

    def get_active_epics(self) -> List[Epic]:
        """Get all active epics."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM epics WHERE status = 'active' ORDER BY epic_num"
            )
            return [Epic(**dict(row)) for row in cursor.fetchall()]

    # ==================== SPRINT OPERATIONS ====================

    def create_sprint(self, sprint_num: int, start_date: str, end_date: str) -> Sprint:
        """Create new sprint."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sprints (sprint_num, start_date, end_date, status, created_at)
                VALUES (?, ?, ?, 'active', ?)
                """,
                (sprint_num, start_date, end_date, datetime.now().isoformat())
            )
            return self.get_sprint(sprint_num)

    def get_sprint(self, sprint_num: int) -> Sprint:
        """Get sprint with metrics."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM sprints WHERE sprint_num = ?", (sprint_num,))
            row = cursor.fetchone()
            if not row:
                raise RecordNotFoundError(f"Sprint {sprint_num} not found")
            return Sprint(**dict(row))

    def assign_story_to_sprint(self, epic_num: int, story_num: int, sprint_num: int) -> Story:
        """Assign story to sprint."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE stories SET sprint = ?, updated_at = ? WHERE epic = ? AND story_num = ?",
                (sprint_num, datetime.now().isoformat(), epic_num, story_num)
            )
            return self.get_story(epic_num, story_num)

    def get_sprint_stories(self, sprint_num: int) -> List[Story]:
        """Get all stories in sprint."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM stories WHERE sprint = ? ORDER BY epic, story_num",
                (sprint_num,)
            )
            return [Story(**dict(row)) for row in cursor.fetchall()]

    def get_sprint_velocity(self, sprint_num: int) -> int:
        """Calculate sprint velocity (completed points)."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT SUM(points) as velocity FROM stories WHERE sprint = ? AND status = 'completed'",
                (sprint_num,)
            )
            row = cursor.fetchone()
            return row['velocity'] or 0

    def get_current_sprint(self) -> Optional[Sprint]:
        """Get currently active sprint."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM sprints WHERE status = 'active' ORDER BY sprint_num DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return Sprint(**dict(row)) if row else None

    # ==================== WORKFLOW OPERATIONS ====================

    def track_workflow_execution(
        self,
        workflow_id: str,
        epic_num: int,
        story_num: int,
        workflow_name: str
    ) -> WorkflowExecution:
        """Record workflow execution."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO workflow_executions (workflow_id, epic, story_num, workflow_name, status, started_at)
                VALUES (?, ?, ?, ?, 'running', ?)
                """,
                (workflow_id, epic_num, story_num, workflow_name, datetime.now().isoformat())
            )
            return self.get_workflow_execution(workflow_id)

    def update_workflow_status(self, workflow_id: str, status: str, result: Optional[Dict[str, Any]] = None):
        """Update workflow execution status."""
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE workflow_executions
                SET status = ?, completed_at = ?, result = ?
                WHERE workflow_id = ?
                """,
                (status, datetime.now().isoformat(), str(result) if result else None, workflow_id)
            )

    def get_story_workflow_history(self, epic_num: int, story_num: int) -> List[WorkflowExecution]:
        """Get workflow execution history for story."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM workflow_executions
                WHERE epic = ? AND story_num = ?
                ORDER BY started_at DESC
                """,
                (epic_num, story_num)
            )
            return [WorkflowExecution(**dict(row)) for row in cursor.fetchall()]

    def get_workflow_execution(self, workflow_id: str) -> WorkflowExecution:
        """Get workflow execution by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM workflow_executions WHERE workflow_id = ?",
                (workflow_id,)
            )
            row = cursor.fetchone()
            if not row:
                raise RecordNotFoundError(f"Workflow execution {workflow_id} not found")
            return WorkflowExecution(**dict(row))
```

### Data Models

```python
# gao_dev/core/state/models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Story:
    """Story data model."""
    id: int
    epic: int
    story_num: int
    title: str
    status: str
    owner: Optional[str] = None
    points: int = 0
    priority: str = "P1"
    sprint: Optional[int] = None
    created_at: str = ""
    updated_at: str = ""

    @property
    def full_id(self) -> str:
        """Return full story ID (e.g., '12.3')."""
        return f"{self.epic}.{self.story_num}"

@dataclass
class Epic:
    """Epic data model with computed progress."""
    id: int
    epic_num: int
    title: str
    feature: str
    status: str
    total_points: int = 0
    completed_points: int = 0
    progress: float = 0.0
    created_at: str = ""
    updated_at: str = ""

@dataclass
class Sprint:
    """Sprint data model."""
    id: int
    sprint_num: int
    start_date: str
    end_date: str
    status: str
    created_at: str = ""

@dataclass
class WorkflowExecution:
    """Workflow execution record."""
    id: int
    workflow_id: str
    epic: int
    story_num: int
    workflow_name: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    result: Optional[str] = None
```

**Files to Create:**
- `gao_dev/core/state/__init__.py`
- `gao_dev/core/state/state_tracker.py`
- `gao_dev/core/state/models.py`
- `gao_dev/core/state/exceptions.py`
- `tests/core/state/test_state_tracker.py`
- `tests/core/state/test_models.py`

**Dependencies:** Story 15.1 (State Database Schema)

---

## Testing Requirements

### Unit Tests

**Story Operations:**
- [ ] Test `create_story()` with all parameters
- [ ] Test `get_story()` retrieves correct story
- [ ] Test `get_story()` raises RecordNotFoundError for missing story
- [ ] Test `update_story_status()` updates status and timestamp
- [ ] Test `get_stories_by_status()` filters correctly
- [ ] Test `get_stories_by_epic()` returns all stories in order
- [ ] Test `get_stories_by_sprint()` filters by sprint
- [ ] Test pagination with limit and offset

**Epic Operations:**
- [ ] Test `create_epic()` creates epic with default values
- [ ] Test `get_epic()` computes progress correctly
- [ ] Test `get_epic_progress()` returns percentage
- [ ] Test `update_epic_points()` updates totals
- [ ] Test `get_active_epics()` filters by status
- [ ] Test `get_epics_by_feature()` filters correctly

**Sprint Operations:**
- [ ] Test `create_sprint()` creates sprint
- [ ] Test `assign_story_to_sprint()` updates sprint field
- [ ] Test `unassign_story_from_sprint()` clears sprint
- [ ] Test `get_sprint_stories()` returns all stories
- [ ] Test `get_sprint_velocity()` calculates correctly
- [ ] Test `get_current_sprint()` returns active sprint
- [ ] Test `get_sprint_completion_rate()` calculates rate

**Workflow Operations:**
- [ ] Test `track_workflow_execution()` creates record
- [ ] Test `update_workflow_status()` updates status
- [ ] Test `get_story_workflow_history()` returns history ordered by time
- [ ] Test `get_failed_workflows()` filters by status
- [ ] Test `get_workflow_metrics()` aggregates correctly

**Data Integrity:**
- [ ] Test thread-safe concurrent operations
- [ ] Test transaction rollback on error
- [ ] Test foreign key enforcement
- [ ] Test prepared statements prevent SQL injection
- [ ] Test enum validation for status and priority
- [ ] Test automatic timestamp updates

### Integration Tests
- [ ] Create story, assign to sprint, update status (end-to-end)
- [ ] Create epic, create multiple stories, calculate progress
- [ ] Track workflow execution, update status, query history
- [ ] Batch operations with multiple inserts
- [ ] Query performance with large datasets (1000+ records)

### Performance Tests
- [ ] Single query completes in <50ms (p99)
- [ ] Batch insert 100 stories in <500ms
- [ ] Complex join query completes in <100ms
- [ ] Concurrent operations maintain consistency

**Test Coverage:** >80%

---

## Documentation Requirements

- [ ] Code documentation (docstrings) for all methods
- [ ] API documentation with examples for each operation
- [ ] Data model documentation with field descriptions
- [ ] Transaction and thread-safety usage guide
- [ ] Error handling patterns and custom exceptions
- [ ] Performance optimization tips (indexing, batching)
- [ ] Example usage patterns for common scenarios

---

## Implementation Details

### Development Approach

**Phase 1: Core Infrastructure**
1. Implement base StateTracker class with connection management
2. Add Story CRUD operations
3. Add Epic CRUD operations
4. Add comprehensive error handling

**Phase 2: Extended Operations**
1. Implement Sprint operations
2. Implement Workflow tracking
3. Add batch operations support
4. Add pagination support

**Phase 3: Quality & Performance**
1. Add thread-safety testing
2. Add performance benchmarks
3. Optimize query performance
4. Add integration tests

### Quality Gates
- [ ] All unit tests pass with >80% coverage
- [ ] Performance benchmarks meet targets (<50ms queries)
- [ ] Thread-safety verified with concurrent tests
- [ ] Code review completed
- [ ] Documentation complete

---

## Definition of Done

- [ ] All acceptance criteria met
- [ ] All CRUD operations implemented and tested
- [ ] Data models defined with proper typing
- [ ] Thread-safe operations verified
- [ ] Transaction support implemented with rollback
- [ ] Tests passing (>80% coverage)
- [ ] Performance benchmarks met (<50ms queries)
- [ ] Error handling comprehensive with custom exceptions
- [ ] Code reviewed and approved
- [ ] Documentation complete with examples
- [ ] No regression in existing functionality
- [ ] Committed with atomic commit message:
  ```
  feat(epic-15): implement Story 15.2 - StateTracker Implementation

  - Implement StateTracker class with comprehensive CRUD operations
  - Add Story, Epic, Sprint, WorkflowExecution operations
  - Implement thread-safe connection management
  - Add transaction support with rollback
  - Create typed data models (Story, Epic, Sprint, WorkflowExecution)
  - Add comprehensive unit tests (>80% coverage)
  - Performance optimizations (<50ms queries)

  Generated with GAO-Dev
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
