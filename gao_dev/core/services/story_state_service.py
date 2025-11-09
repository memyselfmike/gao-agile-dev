"""Story State Service - Fast story status queries.

This service provides CRUD operations for story state management with
optimized queries for <5ms performance.

Epic: 24 - State Tables & Tracker
Story: 24.3 - Implement StoryStateService

Design Pattern: Service Layer
Dependencies: sqlite3, structlog
"""

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

import structlog

logger = structlog.get_logger()


class StoryStateService:
    """
    Service for story state management with fast queries.

    Provides CRUD operations for story_state table with thread-safe
    database access and <5ms query performance.

    Example:
        ```python
        service = StoryStateService(db_path=Path(".gao-dev/documents.db"))

        # Create story
        story = service.create(
            epic_num=1,
            story_num=1,
            title="User login endpoint",
            status="pending",
            priority="P0"
        )

        # Transition status
        service.transition(
            epic_num=1,
            story_num=1,
            new_status="in_progress",
            assignee="amelia"
        )

        # Complete story
        service.complete(epic_num=1, story_num=1, actual_hours=8.5)
        ```
    """

    def __init__(self, db_path: Path):
        """
        Initialize story state service.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._local = threading.local()
        self.logger = logger.bind(service="story_state")

    @contextmanager
    def _get_connection(self):
        """Get thread-local database connection with transaction handling."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA foreign_keys = ON")

        try:
            yield self._local.conn
        except Exception:
            self._local.conn.rollback()
            raise
        else:
            self._local.conn.commit()

    def create(
        self,
        epic_num: int,
        story_num: int,
        title: str,
        status: str = "pending",
        assignee: Optional[str] = None,
        priority: str = "P2",
        estimate_hours: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create new story state record.

        Args:
            epic_num: Epic number
            story_num: Story number
            title: Story title
            status: Story status (pending, in_progress, review, testing, completed, blocked)
            assignee: Assignee name
            priority: Priority (P0, P1, P2, P3)
            estimate_hours: Estimated hours
            metadata: Additional metadata as JSON

        Returns:
            Created story record as dictionary

        Raises:
            ValueError: If story already exists or parameters invalid
        """
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO story_state (
                        epic_num, story_num, title, status, assignee, priority,
                        estimate_hours, created_at, updated_at, metadata
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        epic_num,
                        story_num,
                        title,
                        status,
                        assignee,
                        priority,
                        estimate_hours,
                        now,
                        now,
                        json.dumps(metadata) if metadata else None,
                    ),
                )

                self.logger.info(
                    "story_created",
                    epic_num=epic_num,
                    story_num=story_num,
                    title=title,
                    status=status,
                    assignee=assignee,
                )

                return self.get(epic_num, story_num)

            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    raise ValueError(
                        f"Story {epic_num}.{story_num} already exists"
                    ) from e
                elif "CHECK constraint failed" in str(e):
                    raise ValueError(f"Invalid parameter value") from e
                elif "FOREIGN KEY constraint failed" in str(e):
                    raise ValueError(f"Epic {epic_num} does not exist") from e
                raise

    def get(self, epic_num: int, story_num: int) -> Dict[str, Any]:
        """
        Get story state by epic and story number.

        Args:
            epic_num: Epic number
            story_num: Story number

        Returns:
            Story record as dictionary

        Raises:
            ValueError: If story not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM story_state WHERE epic_num = ? AND story_num = ?",
                (epic_num, story_num),
            )

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Story {epic_num}.{story_num} not found")

            return dict(row)

    def transition(
        self,
        epic_num: int,
        story_num: int,
        new_status: str,
        assignee: Optional[str] = None,
        blocked_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transition story to new status.

        Automatically sets started_at when moving to in_progress.

        Args:
            epic_num: Epic number
            story_num: Story number
            new_status: New status
            assignee: Optional assignee update
            blocked_reason: Reason if blocked

        Returns:
            Updated story record

        Raises:
            ValueError: If story not found
        """
        # Get current story
        story = self.get(epic_num, story_num)

        # Determine timestamps
        now = datetime.utcnow().isoformat()
        started_at = story["started_at"]

        # Auto-set started_at if moving to in_progress
        if new_status == "in_progress" and not started_at:
            started_at = now

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build update query dynamically
            updates = ["status = ?", "started_at = ?", "updated_at = ?"]
            params = [new_status, started_at, now]

            if assignee is not None:
                updates.append("assignee = ?")
                params.append(assignee)

            if blocked_reason is not None:
                updates.append("blocked_reason = ?")
                params.append(blocked_reason)

            params.extend([epic_num, story_num])

            cursor.execute(
                f"""
                UPDATE story_state
                SET {', '.join(updates)}
                WHERE epic_num = ? AND story_num = ?
                """,
                params,
            )

            self.logger.info(
                "story_transitioned",
                epic_num=epic_num,
                story_num=story_num,
                old_status=story["status"],
                new_status=new_status,
                assignee=assignee,
            )

            return self.get(epic_num, story_num)

    def complete(
        self,
        epic_num: int,
        story_num: int,
        actual_hours: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Mark story as completed.

        Sets status to 'completed' and records actual hours and completion time.

        Args:
            epic_num: Epic number
            story_num: Story number
            actual_hours: Actual hours spent

        Returns:
            Updated story record

        Example:
            ```python
            service.complete(epic_num=1, story_num=1, actual_hours=8.5)
            ```
        """
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE story_state
                SET status = 'completed',
                    actual_hours = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE epic_num = ? AND story_num = ?
                """,
                (actual_hours, now, now, epic_num, story_num),
            )

            if cursor.rowcount == 0:
                raise ValueError(f"Story {epic_num}.{story_num} not found")

            self.logger.info(
                "story_completed",
                epic_num=epic_num,
                story_num=story_num,
                actual_hours=actual_hours,
            )

            return self.get(epic_num, story_num)

    def list_by_epic(self, epic_num: int) -> List[Dict[str, Any]]:
        """
        List all stories for an epic.

        Args:
            epic_num: Epic number

        Returns:
            List of story records ordered by story_num
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM story_state
                WHERE epic_num = ?
                ORDER BY story_num ASC
                """,
                (epic_num,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def list_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        List all stories with given status.

        Args:
            status: Status to filter by

        Returns:
            List of story records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM story_state
                WHERE status = ?
                ORDER BY epic_num ASC, story_num ASC
                """,
                (status,),
            )

            return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        """Close database connection for current thread."""
        if hasattr(self._local, "conn"):
            try:
                self._local.conn.close()
            except Exception:
                pass
            delattr(self._local, "conn")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close connections."""
        self.close()
