"""StateTracker implementation for GAO-Dev state management.

Provides thread-safe CRUD operations for stories, epics, sprints, and workflows
with transaction support, connection pooling, and rich query capabilities.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from .models import Story, Epic, Sprint, WorkflowExecution
from .exceptions import (
    StateTrackerError,
    RecordNotFoundError,
    ValidationError,
    DatabaseConnectionError,
)


class StateTracker:
    """Thread-safe state tracker for GAO-Dev with comprehensive CRUD operations.

    Provides the data access layer for stories, epics, sprints, and workflows
    with transaction support and connection pooling. All operations are thread-safe
    and use prepared statements for SQL injection prevention.

    Attributes:
        db_path: Path to SQLite database file

    Example:
        >>> tracker = StateTracker(Path("state.db"))
        >>> story = tracker.create_story(
        ...     epic_num=1,
        ...     story_num=1,
        ...     title="Implement feature"
        ... )
        >>> story.status
        'pending'
    """

    def __init__(self, db_path: Path):
        """Initialize StateTracker.

        Args:
            db_path: Path to SQLite database file

        Raises:
            DatabaseConnectionError: If database file does not exist
        """
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self) -> None:
        """Ensure database file exists.

        Raises:
            DatabaseConnectionError: If database file not found
        """
        if not self.db_path.exists():
            raise DatabaseConnectionError(f"Database not found: {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Get database connection with automatic cleanup and transaction support.

        Yields:
            sqlite3.Connection: Database connection with row factory enabled

        Raises:
            StateTrackerError: On database operation failure (with rollback)
        """
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False
            )  # Thread-safe
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise StateTrackerError(f"Database error: {e}") from e
        finally:
            if conn:
                conn.close()

    def _get_story_sprint(self, conn: sqlite3.Connection, epic_num: int, story_num: int) -> Optional[int]:
        """Helper to get sprint assignment for a story.

        Args:
            conn: Database connection
            epic_num: Epic number
            story_num: Story number

        Returns:
            Sprint number if assigned, None otherwise
        """
        cursor = conn.execute(
            "SELECT sprint_num FROM story_assignments WHERE epic_num = ? AND story_num = ?",
            (epic_num, story_num)
        )
        row = cursor.fetchone()
        return row["sprint_num"] if row else None

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
        sprint: Optional[int] = None,
    ) -> Story:
        """Create new story.

        Args:
            epic_num: Epic number
            story_num: Story number within epic
            title: Story title
            status: Story status (default: 'pending')
            owner: Story owner/agent
            points: Story points estimate
            priority: Priority level (P0-P3)
            sprint: Sprint number assignment (optional)

        Returns:
            Created Story instance

        Raises:
            ValidationError: If status or priority invalid
            StateTrackerError: On database error
        """
        # Validate status
        valid_statuses = ["pending", "in_progress", "done", "blocked", "cancelled"]
        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid status '{status}'. Must be one of: {valid_statuses}"
            )

        # Validate priority
        valid_priorities = ["P0", "P1", "P2", "P3"]
        if priority not in valid_priorities:
            raise ValidationError(
                f"Invalid priority '{priority}'. Must be one of: {valid_priorities}"
            )

        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO stories (
                    epic_num, story_num, title, status, owner,
                    points, priority, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (epic_num, story_num, title, status, owner, points, priority, now, now),
            )

            # If sprint provided, create assignment
            if sprint is not None:
                conn.execute(
                    "INSERT INTO story_assignments (sprint_num, epic_num, story_num) VALUES (?, ?, ?)",
                    (sprint, epic_num, story_num)
                )

        # Query in new transaction to get the committed row
        return self.get_story(epic_num, story_num)

    def get_story(self, epic_num: int, story_num: int) -> Story:
        """Get story by epic and story number.

        Args:
            epic_num: Epic number
            story_num: Story number

        Returns:
            Story instance

        Raises:
            RecordNotFoundError: If story not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, epic_num, story_num, title, status, owner,
                       points, priority, created_at, updated_at
                FROM stories WHERE epic_num = ? AND story_num = ?
                """,
                (epic_num, story_num),
            )
            row = cursor.fetchone()
            if not row:
                raise RecordNotFoundError(f"Story {epic_num}.{story_num} not found")

            # Convert row to dict, handling column mapping
            story_data = dict(row)
            # Map epic_num to epic for dataclass
            story_data["epic"] = story_data.pop("epic_num")

            # Get sprint assignment
            story_data["sprint"] = self._get_story_sprint(conn, epic_num, story_num)

            return Story(**story_data)

    def update_story_status(
        self, epic_num: int, story_num: int, status: str
    ) -> Story:
        """Update story status with automatic timestamp update.

        Args:
            epic_num: Epic number
            story_num: Story number
            status: New status

        Returns:
            Updated Story instance

        Raises:
            ValidationError: If status invalid
            RecordNotFoundError: If story not found
        """
        # Validate status
        valid_statuses = ["pending", "in_progress", "done", "blocked", "cancelled"]
        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid status '{status}'. Must be one of: {valid_statuses}"
            )

        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE stories SET status = ?, updated_at = ? WHERE epic_num = ? AND story_num = ?",
                (status, datetime.now().isoformat(), epic_num, story_num),
            )
            if cursor.rowcount == 0:
                raise RecordNotFoundError(f"Story {epic_num}.{story_num} not found")
        # Query in new transaction to get the updated row
        return self.get_story(epic_num, story_num)

    def update_story_owner(
        self, epic_num: int, story_num: int, owner: str
    ) -> Story:
        """Assign owner to story.

        Args:
            epic_num: Epic number
            story_num: Story number
            owner: Owner/agent name

        Returns:
            Updated Story instance

        Raises:
            RecordNotFoundError: If story not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE stories SET owner = ?, updated_at = ? WHERE epic_num = ? AND story_num = ?",
                (owner, datetime.now().isoformat(), epic_num, story_num),
            )
            if cursor.rowcount == 0:
                raise RecordNotFoundError(f"Story {epic_num}.{story_num} not found")
        # Query in new transaction to get the updated row
        return self.get_story(epic_num, story_num)

    def update_story_points(
        self, epic_num: int, story_num: int, points: int
    ) -> Story:
        """Update story points.

        Args:
            epic_num: Epic number
            story_num: Story number
            points: New story points value

        Returns:
            Updated Story instance

        Raises:
            RecordNotFoundError: If story not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE stories SET points = ?, updated_at = ? WHERE epic_num = ? AND story_num = ?",
                (points, datetime.now().isoformat(), epic_num, story_num),
            )
            if cursor.rowcount == 0:
                raise RecordNotFoundError(f"Story {epic_num}.{story_num} not found")
        # Query in new transaction to get the updated row
        return self.get_story(epic_num, story_num)

    def get_stories_by_status(
        self, status: str, limit: int = 100, offset: int = 0
    ) -> List[Story]:
        """Get stories by status with pagination.

        Args:
            status: Story status to filter by
            limit: Maximum number of results (default: 100)
            offset: Number of results to skip (default: 0)

        Returns:
            List of Story instances
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, epic_num, story_num, title, status, owner,
                       points, priority, created_at, updated_at
                FROM stories WHERE status = ? ORDER BY epic_num, story_num LIMIT ? OFFSET ?
                """,
                (status, limit, offset),
            )
            stories = []
            for row in cursor.fetchall():
                story_data = dict(row)
                epic = story_data.pop("epic_num")
                story_data["epic"] = epic
                story_num = story_data["story_num"]
                story_data["sprint"] = self._get_story_sprint(conn, epic, story_num)
                stories.append(Story(**story_data))
            return stories

    def get_stories_by_epic(self, epic_num: int) -> List[Story]:
        """Get all stories in epic, ordered by story number.

        Args:
            epic_num: Epic number

        Returns:
            List of Story instances ordered by story_num
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, epic_num, story_num, title, status, owner,
                       points, priority, created_at, updated_at
                FROM stories WHERE epic_num = ? ORDER BY story_num
                """,
                (epic_num,),
            )
            stories = []
            for row in cursor.fetchall():
                story_data = dict(row)
                story_data["epic"] = story_data.pop("epic_num")
                story_num = story_data["story_num"]
                story_data["sprint"] = self._get_story_sprint(conn, epic_num, story_num)
                stories.append(Story(**story_data))
            return stories

    def get_stories_by_sprint(self, sprint_num: int) -> List[Story]:
        """Get all stories in sprint.

        Args:
            sprint_num: Sprint number

        Returns:
            List of Story instances in the sprint
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT s.* FROM stories s
                JOIN story_assignments sa ON s.epic_num = sa.epic_num AND s.story_num = sa.story_num
                WHERE sa.sprint_num = ?
                ORDER BY s.epic_num, s.story_num
                """,
                (sprint_num,),
            )
            stories = []
            for row in cursor.fetchall():
                story_data = dict(row)
                story_data["epic"] = story_data.pop("epic_num")
                story_data["sprint"] = sprint_num  # We know it's assigned to this sprint
                stories.append(Story(**story_data))
            return stories

    def get_stories_in_progress(self) -> List[Story]:
        """Get all stories with status 'in_progress'.

        Returns:
            List of in-progress Story instances
        """
        return self.get_stories_by_status("in_progress")

    def get_blocked_stories(self) -> List[Story]:
        """Get all stories with status 'blocked'.

        Returns:
            List of blocked Story instances
        """
        return self.get_stories_by_status("blocked")

    # ==================== EPIC OPERATIONS ====================

    def create_epic(
        self, epic_num: int, title: str, feature: str, total_points: int = 0
    ) -> Epic:
        """Create new epic.

        Args:
            epic_num: Epic number (must be unique)
            title: Epic title
            feature: Feature name
            total_points: Total story points (default: 0)

        Returns:
            Created Epic instance

        Raises:
            StateTrackerError: On database error (e.g., duplicate epic_num)
        """
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO epics (
                    epic_num, name, feature, status,
                    total_points, completed_points, created_at, updated_at
                )
                VALUES (?, ?, ?, 'active', ?, 0, ?, ?)
                """,
                (epic_num, title, feature, total_points, now, now),
            )
        # Query in new transaction to get the committed row
        return self.get_epic(epic_num)

    def get_epic(self, epic_num: int) -> Epic:
        """Get epic with computed progress percentage.

        Args:
            epic_num: Epic number

        Returns:
            Epic instance with progress calculated

        Raises:
            RecordNotFoundError: If epic not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, epic_num, name, feature, status,
                       total_points, completed_points, created_at, updated_at
                FROM epics WHERE epic_num = ?
                """,
                (epic_num,)
            )
            row = cursor.fetchone()
            if not row:
                raise RecordNotFoundError(f"Epic {epic_num} not found")

            epic_data = dict(row)
            # Map 'name' to 'title' for dataclass
            epic_data["title"] = epic_data.pop("name")
            # Progress is computed in Epic.__post_init__
            return Epic(**epic_data)

    def get_epic_progress(self, epic_num: int) -> float:
        """Calculate epic completion percentage.

        Args:
            epic_num: Epic number

        Returns:
            Progress percentage (0.0 to 100.0)

        Raises:
            RecordNotFoundError: If epic not found
        """
        epic = self.get_epic(epic_num)
        return epic.progress

    def update_epic_points(
        self, epic_num: int, total: int, completed: int
    ) -> Epic:
        """Update epic total and completed points.

        Args:
            epic_num: Epic number
            total: Total story points
            completed: Completed story points

        Returns:
            Updated Epic instance

        Raises:
            RecordNotFoundError: If epic not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE epics
                SET total_points = ?, completed_points = ?, updated_at = ?
                WHERE epic_num = ?
                """,
                (total, completed, datetime.now().isoformat(), epic_num),
            )
            if cursor.rowcount == 0:
                raise RecordNotFoundError(f"Epic {epic_num} not found")
            return self.get_epic(epic_num)

    def update_epic_status(self, epic_num: int, status: str) -> Epic:
        """Update epic status.

        Args:
            epic_num: Epic number
            status: New status

        Returns:
            Updated Epic instance

        Raises:
            ValidationError: If status invalid
            RecordNotFoundError: If epic not found
        """
        valid_statuses = ["planned", "active", "completed", "cancelled"]
        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid status '{status}'. Must be one of: {valid_statuses}"
            )

        with self._get_connection() as conn:
            cursor = conn.execute(
                "UPDATE epics SET status = ?, updated_at = ? WHERE epic_num = ?",
                (status, datetime.now().isoformat(), epic_num),
            )
            if cursor.rowcount == 0:
                raise RecordNotFoundError(f"Epic {epic_num} not found")
            return self.get_epic(epic_num)

    def get_active_epics(self) -> List[Epic]:
        """Get all epics with status 'active'.

        Returns:
            List of active Epic instances
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, epic_num, name, feature, status,
                       total_points, completed_points, created_at, updated_at
                FROM epics WHERE status = 'active' ORDER BY epic_num
                """
            )
            epics = []
            for row in cursor.fetchall():
                epic_data = dict(row)
                epic_data["title"] = epic_data.pop("name")
                epics.append(Epic(**epic_data))
            return epics

    def get_epics_by_feature(self, feature: str) -> List[Epic]:
        """Get all epics for a feature.

        Args:
            feature: Feature name

        Returns:
            List of Epic instances for the feature
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, epic_num, name, feature, status,
                       total_points, completed_points, created_at, updated_at
                FROM epics WHERE feature = ? ORDER BY epic_num
                """,
                (feature,),
            )
            epics = []
            for row in cursor.fetchall():
                epic_data = dict(row)
                epic_data["title"] = epic_data.pop("name")
                epics.append(Epic(**epic_data))
            return epics

    def get_epic_velocity(self, epic_num: int) -> float:
        """Calculate average story completion rate for epic.

        Calculates velocity as: completed_stories / total_stories

        Args:
            epic_num: Epic number

        Returns:
            Velocity as decimal (0.0 to 1.0)

        Raises:
            RecordNotFoundError: If epic not found
        """
        # Verify epic exists
        self.get_epic(epic_num)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed
                FROM stories
                WHERE epic_num = ?
                """,
                (epic_num,),
            )
            row = cursor.fetchone()
            total = row["total"] or 0
            completed = row["completed"] or 0

            if total == 0:
                return 0.0
            return completed / total

    # ==================== SPRINT OPERATIONS ====================

    def create_sprint(
        self, sprint_num: int, start_date: str, end_date: str
    ) -> Sprint:
        """Create new sprint.

        Args:
            sprint_num: Sprint number (must be unique)
            start_date: Sprint start date (ISO format)
            end_date: Sprint end date (ISO format)

        Returns:
            Created Sprint instance

        Raises:
            ValidationError: If end_date <= start_date
            StateTrackerError: On database error
        """
        if end_date <= start_date:
            raise ValidationError("end_date must be after start_date")

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sprints (
                    sprint_num, name, start_date, end_date, status, created_at
                )
                VALUES (?, ?, ?, ?, 'active', ?)
                """,
                (sprint_num, f"Sprint {sprint_num}", start_date, end_date, datetime.now().isoformat()),
            )
        # Query in new transaction to get the committed row
        return self.get_sprint(sprint_num)

    def get_sprint(self, sprint_num: int) -> Sprint:
        """Get sprint by number.

        Args:
            sprint_num: Sprint number

        Returns:
            Sprint instance

        Raises:
            RecordNotFoundError: If sprint not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, sprint_num, name, start_date, end_date, status, created_at
                FROM sprints WHERE sprint_num = ?
                """,
                (sprint_num,)
            )
            row = cursor.fetchone()
            if not row:
                raise RecordNotFoundError(f"Sprint {sprint_num} not found")
            return Sprint(**dict(row))

    def assign_story_to_sprint(
        self, epic_num: int, story_num: int, sprint_num: int
    ) -> Story:
        """Assign story to sprint.

        Args:
            epic_num: Epic number
            story_num: Story number
            sprint_num: Sprint number

        Returns:
            Updated Story instance

        Raises:
            RecordNotFoundError: If story or sprint not found
        """
        # Verify sprint exists
        self.get_sprint(sprint_num)

        # Verify story exists
        story = self.get_story(epic_num, story_num)

        with self._get_connection() as conn:
            # Delete existing assignment if any
            conn.execute(
                "DELETE FROM story_assignments WHERE epic_num = ? AND story_num = ?",
                (epic_num, story_num)
            )

            # Create new assignment
            conn.execute(
                "INSERT INTO story_assignments (sprint_num, epic_num, story_num) VALUES (?, ?, ?)",
                (sprint_num, epic_num, story_num)
            )

            # Update story timestamp
            conn.execute(
                "UPDATE stories SET updated_at = ? WHERE epic_num = ? AND story_num = ?",
                (datetime.now().isoformat(), epic_num, story_num)
            )

            return self.get_story(epic_num, story_num)

    def unassign_story_from_sprint(
        self, epic_num: int, story_num: int
    ) -> Story:
        """Remove story from sprint assignment.

        Args:
            epic_num: Epic number
            story_num: Story number

        Returns:
            Updated Story instance

        Raises:
            RecordNotFoundError: If story not found
        """
        # Verify story exists
        story = self.get_story(epic_num, story_num)

        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM story_assignments WHERE epic_num = ? AND story_num = ?",
                (epic_num, story_num)
            )

            # Update story timestamp
            conn.execute(
                "UPDATE stories SET updated_at = ? WHERE epic_num = ? AND story_num = ?",
                (datetime.now().isoformat(), epic_num, story_num)
            )

            return self.get_story(epic_num, story_num)

    def get_sprint_stories(self, sprint_num: int) -> List[Story]:
        """Get all stories in sprint.

        Args:
            sprint_num: Sprint number

        Returns:
            List of Story instances in the sprint
        """
        return self.get_stories_by_sprint(sprint_num)

    def get_sprint_velocity(self, sprint_num: int) -> int:
        """Calculate sprint velocity (completed story points).

        Args:
            sprint_num: Sprint number

        Returns:
            Total completed story points

        Raises:
            RecordNotFoundError: If sprint not found
        """
        # Verify sprint exists
        self.get_sprint(sprint_num)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COALESCE(SUM(s.points), 0) as velocity
                FROM stories s
                JOIN story_assignments sa ON s.epic_num = sa.epic_num AND s.story_num = sa.story_num
                WHERE sa.sprint_num = ? AND s.status = 'done'
                """,
                (sprint_num,),
            )
            row = cursor.fetchone()
            return row["velocity"] or 0

    def get_sprint_completion_rate(self, sprint_num: int) -> float:
        """Calculate sprint story completion rate.

        Args:
            sprint_num: Sprint number

        Returns:
            Completion rate as decimal (0.0 to 1.0)

        Raises:
            RecordNotFoundError: If sprint not found
        """
        # Verify sprint exists
        self.get_sprint(sprint_num)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN s.status = 'done' THEN 1 ELSE 0 END) as completed
                FROM stories s
                JOIN story_assignments sa ON s.epic_num = sa.epic_num AND s.story_num = sa.story_num
                WHERE sa.sprint_num = ?
                """,
                (sprint_num,),
            )
            row = cursor.fetchone()
            total = row["total"] or 0
            completed = row["completed"] or 0

            if total == 0:
                return 0.0
            return completed / total

    def get_current_sprint(self) -> Optional[Sprint]:
        """Get currently active sprint.

        Returns:
            Active Sprint instance or None if no active sprint
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM sprints WHERE status = 'active' ORDER BY sprint_num DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return Sprint(**dict(row)) if row else None

    def get_sprint_burndown_data(self, sprint_num: int) -> Dict[str, Any]:
        """Get sprint burndown data for visualization.

        Args:
            sprint_num: Sprint number

        Returns:
            Dictionary with burndown metrics:
                - total_points: Total story points in sprint
                - completed_points: Completed story points
                - remaining_points: Remaining story points
                - completion_rate: Story completion rate

        Raises:
            RecordNotFoundError: If sprint not found
        """
        sprint = self.get_sprint(sprint_num)

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COALESCE(SUM(s.points), 0) as total_points,
                    COALESCE(SUM(CASE WHEN s.status = 'done' THEN s.points ELSE 0 END), 0) as completed_points
                FROM stories s
                JOIN story_assignments sa ON s.epic_num = sa.epic_num AND s.story_num = sa.story_num
                WHERE sa.sprint_num = ?
                """,
                (sprint_num,),
            )
            row = cursor.fetchone()
            total_points = row["total_points"] or 0
            completed_points = row["completed_points"] or 0
            remaining_points = total_points - completed_points

            return {
                "sprint_num": sprint_num,
                "total_points": total_points,
                "completed_points": completed_points,
                "remaining_points": remaining_points,
                "completion_rate": self.get_sprint_completion_rate(sprint_num),
            }

    # ==================== WORKFLOW OPERATIONS ====================

    def track_workflow_execution(
        self,
        workflow_id: str,
        epic_num: int,
        story_num: int,
        workflow_name: str,
    ) -> WorkflowExecution:
        """Record workflow execution start.

        Args:
            workflow_id: Unique workflow execution identifier
            epic_num: Epic number
            story_num: Story number
            workflow_name: Name of workflow being executed

        Returns:
            Created WorkflowExecution instance

        Raises:
            StateTrackerError: On database error
        """
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO workflow_executions (
                    workflow_name, epic_num, story_num,
                    status, executor, started_at
                )
                VALUES (?, ?, ?, 'running', ?, ?)
                """,
                (workflow_name, epic_num, story_num, workflow_id, datetime.now().isoformat()),
            )
        # Query in new transaction to get the committed row
        return self.get_workflow_execution(workflow_id)

    def update_workflow_status(
        self,
        workflow_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """Update workflow execution status and result.

        Args:
            workflow_id: Workflow execution identifier
            status: New status (completed, failed, cancelled)
            result: Optional execution result dictionary

        Returns:
            Updated WorkflowExecution instance

        Raises:
            ValidationError: If status invalid
            RecordNotFoundError: If workflow execution not found
        """
        valid_statuses = ["started", "running", "completed", "failed", "cancelled"]
        if status not in valid_statuses:
            raise ValidationError(
                f"Invalid status '{status}'. Must be one of: {valid_statuses}"
            )

        result_str = str(result) if result else None

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE workflow_executions
                SET status = ?, completed_at = ?, output = ?
                WHERE executor = ?
                """,
                (status, datetime.now().isoformat(), result_str, workflow_id),
            )
            if cursor.rowcount == 0:
                raise RecordNotFoundError(
                    f"Workflow execution {workflow_id} not found"
                )
            return self.get_workflow_execution(workflow_id)

    def get_story_workflow_history(
        self, epic_num: int, story_num: int
    ) -> List[WorkflowExecution]:
        """Get workflow execution history for story, ordered by start time.

        Args:
            epic_num: Epic number
            story_num: Story number

        Returns:
            List of WorkflowExecution instances ordered by started_at DESC
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM workflow_executions
                WHERE epic_num = ? AND story_num = ?
                ORDER BY started_at DESC
                """,
                (epic_num, story_num),
            )
            workflows = []
            for row in cursor.fetchall():
                wf_data = dict(row)
                # Map executor to workflow_id for dataclass
                wf_data["workflow_id"] = wf_data.pop("executor")
                wf_data["result"] = wf_data.pop("output")
                # Map epic_num to epic
                wf_data["epic"] = wf_data.pop("epic_num")
                workflows.append(WorkflowExecution(**wf_data))
            return workflows

    def get_workflow_execution(self, workflow_id: str) -> WorkflowExecution:
        """Get workflow execution by ID.

        Args:
            workflow_id: Workflow execution identifier

        Returns:
            WorkflowExecution instance

        Raises:
            RecordNotFoundError: If workflow execution not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM workflow_executions WHERE executor = ?",
                (workflow_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise RecordNotFoundError(
                    f"Workflow execution {workflow_id} not found"
                )

            wf_data = dict(row)
            wf_data["workflow_id"] = wf_data.pop("executor")
            wf_data["result"] = wf_data.pop("output")
            wf_data["epic"] = wf_data.pop("epic_num")
            return WorkflowExecution(**wf_data)

    def get_failed_workflows(self) -> List[WorkflowExecution]:
        """Get all failed workflow executions.

        Returns:
            List of WorkflowExecution instances with status='failed'
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM workflow_executions WHERE status = 'failed' ORDER BY started_at DESC"
            )
            workflows = []
            for row in cursor.fetchall():
                wf_data = dict(row)
                wf_data["workflow_id"] = wf_data.pop("executor")
                wf_data["result"] = wf_data.pop("output")
                wf_data["epic"] = wf_data.pop("epic_num")
                workflows.append(WorkflowExecution(**wf_data))
            return workflows

    def get_workflow_metrics(self, workflow_name: str) -> Dict[str, Any]:
        """Aggregate workflow execution metrics.

        Args:
            workflow_name: Workflow name to analyze

        Returns:
            Dictionary with metrics:
                - total_executions: Total number of executions
                - successful: Number of successful executions
                - failed: Number of failed executions
                - success_rate: Success rate as decimal (0.0 to 1.0)
                - avg_duration_ms: Average duration in milliseconds
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    AVG(duration_ms) as avg_duration
                FROM workflow_executions
                WHERE workflow_name = ?
                """,
                (workflow_name,),
            )
            row = cursor.fetchone()
            total = row["total"] or 0
            successful = row["successful"] or 0
            failed = row["failed"] or 0
            avg_duration = row["avg_duration"] or 0.0

            success_rate = successful / total if total > 0 else 0.0

            return {
                "workflow_name": workflow_name,
                "total_executions": total,
                "successful": successful,
                "failed": failed,
                "success_rate": success_rate,
                "avg_duration_ms": avg_duration,
            }
