"""Action Item Service - Fast action item tracking.

This service provides CRUD operations for action item management with
optimized queries for <5ms performance.

Epic: 24 - State Tables & Tracker
Story: 24.4 - Implement ActionItemService

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


class ActionItemService:
    """
    Service for action item management with fast queries.

    Example:
        ```python
        service = ActionItemService(db_path=Path(".gao-dev/documents.db"))

        # Create action item
        item = service.create(
            title="Update API documentation",
            description="Add authentication examples",
            assignee="john",
            priority="high",
            epic_num=1,
            due_date="2025-11-15"
        )

        # Complete item
        service.complete(item_id=1)

        # Get active items
        active = service.get_active()
        ```
    """

    def __init__(self, db_path: Path):
        """Initialize action item service."""
        self.db_path = Path(db_path)
        self._local = threading.local()
        self.logger = logger.bind(service="action_item")

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
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        assignee: Optional[str] = None,
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        due_date: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create new action item.

        Args:
            title: Item title
            description: Item description
            priority: Priority (high, medium, low)
            assignee: Assignee name
            epic_num: Associated epic number
            story_num: Associated story number
            due_date: Due date (ISO format)
            metadata: Additional metadata

        Returns:
            Created action item record
        """
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO action_items (
                    title, description, status, priority, assignee,
                    epic_num, story_num, due_date, created_at, updated_at, metadata
                )
                VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    description,
                    priority,
                    assignee,
                    epic_num,
                    story_num,
                    due_date,
                    now,
                    now,
                    json.dumps(metadata) if metadata else None,
                ),
            )

            item_id = cursor.lastrowid

            self.logger.info(
                "action_item_created",
                id=item_id,
                title=title,
                priority=priority,
                assignee=assignee,
            )

            return self.get(item_id)

    def get(self, item_id: int) -> Dict[str, Any]:
        """Get action item by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM action_items WHERE id = ?", (item_id,))

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Action item {item_id} not found")

            return dict(row)

    def complete(self, item_id: int) -> Dict[str, Any]:
        """
        Mark action item as completed.

        Args:
            item_id: Action item ID

        Returns:
            Updated action item record
        """
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE action_items
                SET status = 'completed',
                    completed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (now, now, item_id),
            )

            if cursor.rowcount == 0:
                raise ValueError(f"Action item {item_id} not found")

            self.logger.info("action_item_completed", id=item_id)

            return self.get(item_id)

    def get_active(
        self, assignee: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all active (pending/in_progress) action items.

        Args:
            assignee: Optional filter by assignee

        Returns:
            List of active action items
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if assignee:
                cursor.execute(
                    """
                    SELECT * FROM action_items
                    WHERE status IN ('pending', 'in_progress')
                      AND assignee = ?
                    ORDER BY
                        CASE priority
                            WHEN 'high' THEN 1
                            WHEN 'medium' THEN 2
                            WHEN 'low' THEN 3
                        END,
                        due_date ASC
                    """,
                    (assignee,),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM action_items
                    WHERE status IN ('pending', 'in_progress')
                    ORDER BY
                        CASE priority
                            WHEN 'high' THEN 1
                            WHEN 'medium' THEN 2
                            WHEN 'low' THEN 3
                        END,
                        due_date ASC
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
