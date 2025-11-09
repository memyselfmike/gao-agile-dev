"""Epic State Service - Fast epic progress queries.

This service provides CRUD operations for epic state management with
optimized queries for <5ms performance.

Epic: 24 - State Tables & Tracker
Story: 24.2 - Implement EpicStateService

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


class EpicStateService:
    """
    Service for epic state management with fast queries.

    Provides CRUD operations for epic_state table with thread-safe
    database access and <5ms query performance.

    Thread Safety:
        - Uses thread-local storage for database connections
        - Each thread gets its own connection
        - All operations are transaction-safe

    Performance:
        - Connection reuse within threads
        - Parameterized queries
        - Indexed queries for <5ms lookups

    Example:
        ```python
        service = EpicStateService(db_path=Path(".gao-dev/documents.db"))

        # Create epic
        epic = service.create(
            epic_num=1,
            title="User Authentication",
            status="planning",
            total_stories=5
        )

        # Update progress
        service.update_progress(
            epic_num=1,
            completed_stories=2,
            status="in_progress"
        )

        # Archive epic
        service.archive(epic_num=1, reason="Completed")
        ```
    """

    def __init__(self, db_path: Path):
        """
        Initialize epic state service.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._local = threading.local()
        self.logger = logger.bind(service="epic_state")

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
        title: str,
        status: str = "planning",
        total_stories: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create new epic state record.

        Args:
            epic_num: Epic number (unique)
            title: Epic title
            status: Epic status (planning, in_progress, blocked, completed, archived)
            total_stories: Total number of stories in epic
            metadata: Additional metadata as JSON

        Returns:
            Created epic record as dictionary

        Raises:
            ValueError: If epic already exists or status is invalid

        Example:
            ```python
            epic = service.create(
                epic_num=1,
                title="User Authentication",
                status="planning",
                total_stories=5,
                metadata={"priority": "high"}
            )
            ```
        """
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    INSERT INTO epic_state (
                        epic_num, title, status, total_stories, completed_stories,
                        progress_percentage, created_at, updated_at, metadata
                    )
                    VALUES (?, ?, ?, ?, 0, 0.0, ?, ?, ?)
                    """,
                    (
                        epic_num,
                        title,
                        status,
                        total_stories,
                        now,
                        now,
                        json.dumps(metadata) if metadata else None,
                    ),
                )

                self.logger.info(
                    "epic_created",
                    epic_num=epic_num,
                    title=title,
                    status=status,
                    total_stories=total_stories,
                )

                return self.get(epic_num)

            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    raise ValueError(f"Epic {epic_num} already exists") from e
                elif "CHECK constraint failed" in str(e):
                    raise ValueError(f"Invalid status: {status}") from e
                raise

    def get(self, epic_num: int) -> Dict[str, Any]:
        """
        Get epic state by epic number.

        Args:
            epic_num: Epic number

        Returns:
            Epic record as dictionary

        Raises:
            ValueError: If epic not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM epic_state WHERE epic_num = ?", (epic_num,))

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Epic {epic_num} not found")

            return dict(row)

    def update_progress(
        self,
        epic_num: int,
        completed_stories: Optional[int] = None,
        total_stories: Optional[int] = None,
        status: Optional[str] = None,
        blocked_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update epic progress.

        Automatically calculates progress percentage based on completed/total stories.
        Updates timestamps and status as needed.

        Args:
            epic_num: Epic number
            completed_stories: Number of completed stories
            total_stories: Total number of stories (updates count)
            status: New status
            blocked_reason: Reason if blocked

        Returns:
            Updated epic record

        Raises:
            ValueError: If epic not found

        Example:
            ```python
            service.update_progress(
                epic_num=1,
                completed_stories=3,
                total_stories=5,
                status="in_progress"
            )
            ```
        """
        # Get current epic
        epic = self.get(epic_num)

        # Calculate new values
        new_completed = completed_stories if completed_stories is not None else epic["completed_stories"]
        new_total = total_stories if total_stories is not None else epic["total_stories"]
        new_status = status if status is not None else epic["status"]

        # Calculate progress
        progress = (new_completed / new_total * 100.0) if new_total > 0 else 0.0

        # Determine timestamps
        now = datetime.utcnow().isoformat()
        started_at = epic["started_at"]
        completed_at = epic["completed_at"]

        # Auto-set started_at if moving to in_progress
        if new_status == "in_progress" and not started_at:
            started_at = now

        # Auto-set completed_at if moving to completed
        if new_status == "completed" and not completed_at:
            completed_at = now

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE epic_state
                SET completed_stories = ?,
                    total_stories = ?,
                    progress_percentage = ?,
                    status = ?,
                    blocked_reason = ?,
                    started_at = ?,
                    completed_at = ?,
                    updated_at = ?
                WHERE epic_num = ?
                """,
                (
                    new_completed,
                    new_total,
                    progress,
                    new_status,
                    blocked_reason,
                    started_at,
                    completed_at,
                    now,
                    epic_num,
                ),
            )

            self.logger.info(
                "epic_progress_updated",
                epic_num=epic_num,
                completed_stories=new_completed,
                total_stories=new_total,
                progress_percentage=progress,
                status=new_status,
            )

            return self.get(epic_num)

    def archive(self, epic_num: int, reason: str = "Completed") -> Dict[str, Any]:
        """
        Archive an epic.

        Sets status to 'archived' and records reason.

        Args:
            epic_num: Epic number
            reason: Reason for archiving

        Returns:
            Updated epic record

        Example:
            ```python
            service.archive(epic_num=1, reason="All stories completed")
            ```
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()

            cursor.execute(
                """
                UPDATE epic_state
                SET status = 'archived',
                    blocked_reason = ?,
                    updated_at = ?
                WHERE epic_num = ?
                """,
                (reason, now, epic_num),
            )

            if cursor.rowcount == 0:
                raise ValueError(f"Epic {epic_num} not found")

            self.logger.info(
                "epic_archived",
                epic_num=epic_num,
                reason=reason,
            )

            return self.get(epic_num)

    def list_active(self) -> List[Dict[str, Any]]:
        """
        List all active epics (not archived).

        Returns:
            List of active epic records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM epic_state
                WHERE status != 'archived'
                ORDER BY epic_num ASC
                """
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
