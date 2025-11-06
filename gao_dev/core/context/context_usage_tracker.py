"""
Context usage tracker for audit trail.

This module tracks which context was used in prompt resolutions, recording
context keys, workflow IDs, content hashes, and cache hits for audit purposes.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import structlog

logger = structlog.get_logger(__name__)


class ContextUsageTracker:
    """
    Track context usage for audit trail.

    This tracker records every context resolution, storing:
    - Which context key was used
    - Which workflow/epic/story it was used in
    - Content hash (for version tracking)
    - Whether it was a cache hit or miss
    - Timestamp of access

    This enables answering questions like:
    - "What context was used for this workflow execution?"
    - "When was the epic definition last accessed?"
    - "Which workflows used outdated context?"

    Example:
        >>> tracker = ContextUsageTracker(Path("context_usage.db"))
        >>> tracker.record_usage(
        ...     context_key="epic_definition",
        ...     workflow_id="wf-123",
        ...     epic=3,
        ...     story="3.1",
        ...     content_hash="abc123",
        ...     cache_hit=True
        ... )
        >>> history = tracker.get_usage_history("wf-123")
        >>> # Returns list of all context used in workflow

    Args:
        db_path: Path to SQLite database file
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize context usage tracker.

        Creates database and schema if not exists.

        Args:
            db_path: Path to SQLite database file. If None, uses unified gao_dev.db
        """
        if db_path is None:
            # Use unified database from config
            from ..config import get_database_path
            self.db_path = get_database_path()
        else:
            self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema.

        Note: If using unified database (Epic 17), the schema is already created
        by migration 003. This method only creates the schema if it doesn't exist.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            # Check if context_usage table already exists with new schema (Epic 17)
            cursor = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='context_usage'"
            )
            existing_schema = cursor.fetchone()

            if existing_schema and 'artifact_type' in existing_schema[0]:
                # Table exists with new Epic 17 schema, skip creation
                logger.debug(
                    "context_usage_table_exists",
                    db_path=str(self.db_path),
                    message="Using unified database schema"
                )
                return

            # Legacy schema creation (for backward compatibility)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_key TEXT NOT NULL,
                    workflow_id TEXT,
                    epic INTEGER,
                    story TEXT,
                    content_hash TEXT NOT NULL,
                    cache_hit BOOLEAN NOT NULL,
                    accessed_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for common queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflow_id
                ON context_usage(workflow_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_context_key
                ON context_usage(context_key)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_epic_story
                ON context_usage(epic, story)
            """)

            conn.commit()

        logger.debug("context_usage_db_initialized", db_path=str(self.db_path))

    @contextmanager
    def _get_connection(self):
        """
        Get database connection context manager.

        Yields:
            sqlite3.Connection with row factory set to Row
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def record_usage(
        self,
        context_key: str,
        content_hash: str,
        cache_hit: bool,
        workflow_id: Optional[str] = None,
        epic: Optional[int] = None,
        story: Optional[str] = None,
    ) -> None:
        """
        Record context usage in database.

        Args:
            context_key: Context key that was resolved (e.g., "epic_definition")
            content_hash: Hash of content at time of use (for version tracking)
            cache_hit: Whether content was loaded from cache
            workflow_id: ID of workflow that used this context (optional)
            epic: Epic number (optional)
            story: Story identifier (optional)
        """
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO context_usage (
                    context_key, workflow_id, epic, story,
                    content_hash, cache_hit, accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                context_key,
                workflow_id,
                epic,
                story,
                content_hash,
                cache_hit,
                datetime.now().isoformat()
            ))
            conn.commit()

        logger.debug(
            "context_usage_recorded",
            context_key=context_key,
            workflow_id=workflow_id,
            cache_hit=cache_hit
        )

    def get_usage_history(
        self,
        workflow_id: Optional[str] = None,
        context_key: Optional[str] = None,
        epic: Optional[int] = None,
        story: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get context usage history.

        Can filter by workflow_id, context_key, epic, or story.
        Returns most recent entries first.

        Args:
            workflow_id: Filter by workflow ID (optional)
            context_key: Filter by context key (optional)
            epic: Filter by epic number (optional)
            story: Filter by story identifier (optional)
            limit: Maximum number of results (default: 100)

        Returns:
            List of usage records as dicts
        """
        conditions = []
        params = []

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)

        if context_key:
            conditions.append("context_key = ?")
            params.append(context_key)

        if epic is not None:
            conditions.append("epic = ?")
            params.append(epic)

        if story:
            conditions.append("story = ?")
            params.append(story)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        query = f"""
            SELECT * FROM context_usage
            {where_clause}
            ORDER BY accessed_at DESC
            LIMIT ?
        """
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_context_versions(self, context_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get version history for a context key.

        Shows different content hashes used over time, which indicates
        when the context was updated.

        Args:
            context_key: Context key to query
            limit: Maximum number of versions (default: 10)

        Returns:
            List of distinct content hashes with first/last access times
        """
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    content_hash,
                    MIN(accessed_at) as first_accessed,
                    MAX(accessed_at) as last_accessed,
                    COUNT(*) as access_count
                FROM context_usage
                WHERE context_key = ?
                GROUP BY content_hash
                ORDER BY last_accessed DESC
                LIMIT ?
            """, (context_key, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_cache_hit_rate(
        self,
        workflow_id: Optional[str] = None,
        context_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate cache hit rate.

        Args:
            workflow_id: Filter by workflow ID (optional)
            context_key: Filter by context key (optional)

        Returns:
            Dict with total, hits, misses, hit_rate
        """
        conditions = []
        params = []

        if workflow_id:
            conditions.append("workflow_id = ?")
            params.append(workflow_id)

        if context_key:
            conditions.append("context_key = ?")
            params.append(context_key)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) as hits,
                    SUM(CASE WHEN cache_hit = 0 THEN 1 ELSE 0 END) as misses
                FROM context_usage
                {where_clause}
            """, params)

            row = cursor.fetchone()
            total = row['total'] or 0
            hits = row['hits'] or 0
            misses = row['misses'] or 0
            hit_rate = hits / total if total > 0 else 0.0

            return {
                'total': total,
                'hits': hits,
                'misses': misses,
                'hit_rate': hit_rate
            }

    def clear_history(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear usage history.

        Args:
            older_than_days: Only clear entries older than N days (optional)
                           If None, clears all history

        Returns:
            Number of entries deleted
        """
        with self._get_connection() as conn:
            if older_than_days is not None:
                # Calculate cutoff date
                from datetime import timedelta
                cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()

                cursor = conn.execute("""
                    DELETE FROM context_usage
                    WHERE accessed_at < ?
                """, (cutoff,))
            else:
                cursor = conn.execute("DELETE FROM context_usage")

            deleted_count = cursor.rowcount
            conn.commit()

        logger.info("context_usage_cleared", deleted_count=deleted_count)
        return deleted_count
