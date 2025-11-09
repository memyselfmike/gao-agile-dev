"""Learning Index Service - Fast learning indexing and search.

This service provides CRUD operations for learning index with
optimized queries for <5ms performance.

Epic: 24 - State Tables & Tracker
Story: 24.6 - Implement LearningIndexService

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


class LearningIndexService:
    """
    Service for learning index management with fast search.

    Example:
        ```python
        service = LearningIndexService(db_path=Path(".gao-dev/documents.db"))

        # Index learning
        learning = service.index(
            topic="Database migrations",
            category="technical",
            learning="Use numbered migration files for ordering",
            context="Migration 005 implementation",
            source_type="code_review",
            epic_num=24
        )

        # Search learnings
        results = service.search(topic="migrations", category="technical")

        # Supersede outdated learning
        service.supersede(old_id=1, new_id=2)
        ```
    """

    def __init__(self, db_path: Path):
        """Initialize learning index service."""
        self.db_path = Path(db_path)
        self._local = threading.local()
        self.logger = logger.bind(service="learning_index")

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

    def index(
        self,
        topic: str,
        category: str,
        learning: str,
        context: Optional[str] = None,
        source_type: Optional[str] = None,
        epic_num: Optional[int] = None,
        story_num: Optional[int] = None,
        relevance_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Index a new learning.

        Args:
            topic: Learning topic
            category: Category (technical, process, domain, architectural, team)
            learning: Learning text
            context: Context where learning was discovered
            source_type: Source (retrospective, postmortem, code_review, incident, experiment)
            epic_num: Associated epic number
            story_num: Associated story number
            relevance_score: Relevance score (0.0-1.0)
            metadata: Additional metadata

        Returns:
            Created learning record
        """
        now = datetime.utcnow().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO learning_index (
                    topic, category, learning, context, source_type,
                    epic_num, story_num, relevance_score, is_active,
                    indexed_at, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """,
                (
                    topic,
                    category,
                    learning,
                    context,
                    source_type,
                    epic_num,
                    story_num,
                    relevance_score,
                    now,
                    now,
                    json.dumps(metadata) if metadata else None,
                ),
            )

            learning_id = cursor.lastrowid

            self.logger.info(
                "learning_indexed",
                id=learning_id,
                topic=topic,
                category=category,
            )

            return self.get(learning_id)

    def get(self, learning_id: int) -> Dict[str, Any]:
        """Get learning by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learning_index WHERE id = ?", (learning_id,))

            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Learning {learning_id} not found")

            return dict(row)

    def supersede(self, old_id: int, new_id: int) -> Dict[str, Any]:
        """
        Mark a learning as superseded by a newer learning.

        Args:
            old_id: ID of learning to supersede
            new_id: ID of superseding learning

        Returns:
            Updated old learning record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verify new_id exists
            cursor.execute("SELECT id FROM learning_index WHERE id = ?", (new_id,))
            if not cursor.fetchone():
                raise ValueError(f"New learning {new_id} not found")

            # Update old learning
            cursor.execute(
                """
                UPDATE learning_index
                SET superseded_by = ?,
                    is_active = 0
                WHERE id = ?
                """,
                (new_id, old_id),
            )

            if cursor.rowcount == 0:
                raise ValueError(f"Learning {old_id} not found")

            self.logger.info(
                "learning_superseded", old_id=old_id, new_id=new_id
            )

            return self.get(old_id)

    def search(
        self,
        topic: Optional[str] = None,
        category: Optional[str] = None,
        active_only: bool = True,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search learnings.

        Args:
            topic: Optional topic filter (partial match)
            category: Optional category filter (exact match)
            active_only: Only return active learnings (not superseded)
            limit: Maximum number of results

        Returns:
            List of matching learning records ordered by relevance
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            conditions = []
            params = []

            if active_only:
                conditions.append("is_active = 1")

            if topic:
                conditions.append("topic LIKE ?")
                params.append(f"%{topic}%")

            if category:
                conditions.append("category = ?")
                params.append(category)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cursor.execute(
                f"""
                SELECT * FROM learning_index
                WHERE {where_clause}
                ORDER BY relevance_score DESC, indexed_at DESC
                LIMIT ?
                """,
                params + [limit],
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
