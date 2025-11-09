"""Ceremony Service - Fast ceremony summary tracking.

This service provides CRUD operations for ceremony summaries with
optimized queries for <5ms performance.

Epic: 24 - State Tables & Tracker
Story: 24.5 - Implement CeremonyService

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


class CeremonyService:
    """
    Service for ceremony summary management with fast queries.

    Example:
        ```python
        service = CeremonyService(db_path=Path(".gao-dev/documents.db"))

        # Create ceremony summary
        ceremony = service.create_summary(
            ceremony_type="retrospective",
            summary="Completed Epic 24 successfully",
            participants="team",
            decisions="Continue using TDD approach",
            action_items="Document patterns for future epics",
            epic_num=24
        )

        # Get recent ceremonies
        recent = service.get_recent(ceremony_type="retrospective", limit=5)
        ```
    """

    def __init__(self, db_path: Path):
        """Initialize ceremony service."""
        self.db_path = Path(db_path)
        self._local = threading.local()
        self.logger = logger.bind(service="ceremony")

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

    def create_summary(
        self,
        ceremony_type: str,
        summary: str,
        participants: Optional[str] = None,
        decisions: Optional[str] = None,
        action_items: Optional[str] = None,
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        held_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create ceremony summary.

        Args:
            ceremony_type: Type (planning, standup, review, retrospective, refinement)
            summary: Summary text
            participants: Participants list
            decisions: Decisions made
            action_items: Action items identified
            epic_num: Associated epic number
            story_num: Associated story number
            held_at: Ceremony date/time (ISO format, defaults to now)
            metadata: Additional metadata

        Returns:
            Created ceremony record
        """
        now = datetime.utcnow().isoformat()
        held_at = held_at or now

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO ceremony_summaries (
                    ceremony_type, epic_num, story_num, summary,
                    participants, decisions, action_items,
                    held_at, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ceremony_type,
                    epic_num,
                    story_num,
                    summary,
                    participants,
                    decisions,
                    action_items,
                    held_at,
                    now,
                    json.dumps(metadata) if metadata else None,
                ),
            )

            ceremony_id = cursor.lastrowid

            self.logger.info(
                "ceremony_summary_created",
                id=ceremony_id,
                ceremony_type=ceremony_type,
                epic_num=epic_num,
            )

            return self.get(ceremony_id)

    def get(self, ceremony_id: int) -> Dict[str, Any]:
        """Get ceremony summary by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM ceremony_summaries WHERE id = ?", (ceremony_id,)
            )

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Ceremony {ceremony_id} not found")

            return dict(row)

    def get_recent(
        self, ceremony_type: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent ceremony summaries.

        Args:
            ceremony_type: Optional filter by ceremony type
            limit: Maximum number of records to return

        Returns:
            List of ceremony records ordered by held_at DESC
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if ceremony_type:
                cursor.execute(
                    """
                    SELECT * FROM ceremony_summaries
                    WHERE ceremony_type = ?
                    ORDER BY held_at DESC
                    LIMIT ?
                    """,
                    (ceremony_type, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM ceremony_summaries
                    ORDER BY held_at DESC
                    LIMIT ?
                    """,
                    (limit,),
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
