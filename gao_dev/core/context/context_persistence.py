"""
Context persistence layer for WorkflowContext with SQLite storage.

This module provides ContextPersistence class for saving and loading WorkflowContext
to/from SQLite database with versioning, querying, and batch operations.
Optimized for fast reads/writes with comprehensive indexing.
"""

import sqlite3
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
    batch operations. Optimized for fast reads/writes with indexes.

    Features:
    - Save and load WorkflowContext to/from database
    - Automatic versioning on each save (auto-increment)
    - Query operations (by epic, story, feature, status)
    - Batch operations with transaction support
    - JSON serialization for complex fields
    - Comprehensive indexing for fast lookups
    - Context manager for safe connection handling

    Example:
        >>> from pathlib import Path
        >>> persistence = ContextPersistence(db_path=Path("gao_dev.db"))
        >>>
        >>> # Save context
        >>> version = persistence.save_context(context)
        >>> print(f"Saved context version {version}")
        >>>
        >>> # Load context
        >>> loaded = persistence.load_context(workflow_id)
        >>>
        >>> # Get latest for story
        >>> latest = persistence.get_latest_context(epic=12, story=3)
        >>>
        >>> # Query contexts
        >>> active = persistence.get_active_contexts()
        >>> failed = persistence.get_failed_contexts()
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize ContextPersistence.

        Args:
            db_path: Path to SQLite database file. If None, uses unified gao_dev.db
        """
        if db_path is None:
            # Use unified database from config
            from ..config import get_database_path
            self.db_path = get_database_path()
        else:
            self.db_path = db_path
        self._ensure_schema_exists()

    def _ensure_schema_exists(self) -> None:
        """
        Ensure workflow_context table exists with indexes.

        Creates table and indexes if they don't exist. Safe to call multiple times.
        """
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
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_context_workflow_id "
                "ON workflow_context(workflow_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_context_epic_story "
                "ON workflow_context(epic_num, story_num)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_context_status "
                "ON workflow_context(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_context_created_at "
                "ON workflow_context(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_workflow_context_feature "
                "ON workflow_context(feature)"
            )

    @contextmanager
    def _get_connection(self):
        """
        Get database connection with automatic cleanup.

        Context manager that handles connection creation, commit on success,
        rollback on error, and cleanup. Converts sqlite3 errors to PersistenceError.

        Yields:
            sqlite3.Connection: Database connection with row_factory

        Raises:
            PersistenceError: If database operation fails
            ContextNotFoundError: Re-raised without wrapping
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Enable foreign keys (required for CASCADE behavior in SQLite)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except ContextNotFoundError:
            # Re-raise ContextNotFoundError without wrapping
            conn.rollback()
            raise
        except PersistenceError:
            # Re-raise PersistenceError without wrapping
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise PersistenceError(f"Database error: {e}") from e
        finally:
            conn.close()

    def save_context(self, context: WorkflowContext) -> int:
        """
        Save context to database.

        If context with same workflow_id exists, updates and increments version.
        Otherwise, creates new context with version 1.

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
            PersistenceError: If deserialization fails
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

    def get_latest_context(
        self, epic_num: int, story_num: Optional[int] = None
    ) -> Optional[WorkflowContext]:
        """
        Get most recent context for story.

        Returns the latest context (by created_at) for the specified epic and story.
        If story_num is None, returns latest epic-level context.

        Args:
            epic_num: Epic number
            story_num: Story number (optional, None for epic-level)

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

    def get_latest_context_by_status(
        self, epic_num: int, story_num: Optional[int], status: str
    ) -> Optional[WorkflowContext]:
        """
        Get most recent context for story filtered by status.

        Returns the latest context (by created_at) for the specified epic, story,
        and status. Useful for finding the last 'completed' or 'failed' context.

        Args:
            epic_num: Epic number
            story_num: Story number (optional, None for epic-level)
            status: Workflow status (running, completed, failed, paused)

        Returns:
            Latest WorkflowContext with status or None if not found
        """
        with self._get_connection() as conn:
            if story_num is not None:
                cursor = conn.execute(
                    """
                    SELECT context_data FROM workflow_context
                    WHERE epic_num = ? AND story_num = ? AND status = ?
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (epic_num, story_num, status)
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT context_data FROM workflow_context
                    WHERE epic_num = ? AND story_num IS NULL AND status = ?
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (epic_num, status)
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

    def update_context(self, context: WorkflowContext) -> int:
        """
        Update existing context in database.

        This is an alias for save_context() to provide clearer semantics
        when updating an existing context. Increments version number.

        Args:
            context: WorkflowContext to update

        Returns:
            New version number

        Raises:
            ContextNotFoundError: If context doesn't exist
            PersistenceError: If update fails
        """
        # Check if exists first
        if not self.context_exists(context.workflow_id):
            raise ContextNotFoundError(
                f"Cannot update non-existent context: {context.workflow_id}"
            )
        return self.save_context(context)

    def context_exists(self, workflow_id: str) -> bool:
        """
        Check if context exists in database.

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

    def get_context_versions(
        self, epic_num: int, story_num: Optional[int] = None
    ) -> List[WorkflowContext]:
        """
        Get all context versions for story.

        Returns all contexts (versions) for the specified epic and story,
        ordered by version ascending.

        Args:
            epic_num: Epic number
            story_num: Story number (optional, None for epic-level)

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

    def get_context_by_version(self, workflow_id: str, version: int) -> Optional[WorkflowContext]:
        """
        Get specific version of context.

        Since we don't maintain version history (updates replace), this currently
        only returns the current version if it matches. Future enhancement could
        add version history table.

        Args:
            workflow_id: Workflow execution ID
            version: Version number

        Returns:
            WorkflowContext if found with matching version, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT context_data, version FROM workflow_context WHERE workflow_id = ?",
                (workflow_id,)
            )
            row = cursor.fetchone()

            if not row or row['version'] != version:
                return None

            context_json = row['context_data']
            return WorkflowContext.from_json(context_json)

    def get_version_count(self, epic_num: int, story_num: Optional[int] = None) -> int:
        """
        Get total version count for story.

        Returns the count of all contexts (versions) for the specified epic and story.

        Args:
            epic_num: Epic number
            story_num: Story number (optional, None for epic-level)

        Returns:
            Total count of versions
        """
        with self._get_connection() as conn:
            if story_num is not None:
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM workflow_context WHERE epic_num = ? AND story_num = ?",
                    (epic_num, story_num)
                )
            else:
                cursor = conn.execute(
                    "SELECT COUNT(*) as count FROM workflow_context WHERE epic_num = ? AND story_num IS NULL",
                    (epic_num,)
                )

            row = cursor.fetchone()
            return row['count'] if row else 0

    def get_active_contexts(self) -> List[WorkflowContext]:
        """
        Get all active (running) workflow contexts.

        Returns all contexts with status='running', ordered by created_at descending.

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

    def get_failed_contexts(self) -> List[WorkflowContext]:
        """
        Get all failed workflow contexts.

        Returns all contexts with status='failed', ordered by created_at descending.

        Returns:
            List of WorkflowContext instances
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT context_data FROM workflow_context WHERE status = 'failed' ORDER BY created_at DESC"
            )

            contexts = []
            for row in cursor.fetchall():
                context_json = row['context_data']
                contexts.append(WorkflowContext.from_json(context_json))

            return contexts

    def save_contexts(self, contexts: List[WorkflowContext]) -> List[int]:
        """
        Batch save multiple contexts.

        Saves all contexts in a single transaction. If any save fails,
        all changes are rolled back.

        Args:
            contexts: List of WorkflowContext instances

        Returns:
            List of version numbers for each saved context

        Raises:
            PersistenceError: If batch save fails (all changes rolled back)
        """
        versions = []
        with self._get_connection() as conn:
            for context in contexts:
                # Inline save logic for transaction efficiency
                context_json = context.to_json()

                cursor = conn.execute(
                    "SELECT version FROM workflow_context WHERE workflow_id = ?",
                    (context.workflow_id,)
                )
                row = cursor.fetchone()

                if row:
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

                versions.append(version)

        return versions

    def load_contexts(self, workflow_ids: List[str]) -> List[WorkflowContext]:
        """
        Batch load multiple contexts.

        Loads all contexts with the specified workflow IDs. Contexts not found
        are skipped (no error raised).

        Args:
            workflow_ids: List of workflow execution IDs

        Returns:
            List of WorkflowContext instances (may be fewer than requested)
        """
        if not workflow_ids:
            return []

        with self._get_connection() as conn:
            # Build parameterized query
            placeholders = ','.join('?' * len(workflow_ids))
            cursor = conn.execute(
                f"SELECT context_data FROM workflow_context WHERE workflow_id IN ({placeholders})",
                workflow_ids
            )

            contexts = []
            for row in cursor.fetchall():
                context_json = row['context_data']
                contexts.append(WorkflowContext.from_json(context_json))

            return contexts

    def get_contexts_by_epic(self, epic_num: int) -> List[WorkflowContext]:
        """
        Get all contexts for epic.

        Returns all contexts (stories and epic-level) for the specified epic,
        ordered by created_at descending.

        Args:
            epic_num: Epic number

        Returns:
            List of WorkflowContext instances
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT context_data FROM workflow_context WHERE epic_num = ? ORDER BY created_at DESC",
                (epic_num,)
            )

            contexts = []
            for row in cursor.fetchall():
                context_json = row['context_data']
                contexts.append(WorkflowContext.from_json(context_json))

            return contexts

    def get_contexts_by_feature(self, feature: str) -> List[WorkflowContext]:
        """
        Get all contexts for feature.

        Returns all contexts for the specified feature name,
        ordered by created_at descending.

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

    def search_contexts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[WorkflowContext]:
        """
        Generic search with multiple filters and pagination.

        Supports filtering by any combination of:
        - epic_num: Epic number
        - story_num: Story number
        - feature: Feature name
        - workflow_name: Workflow name
        - status: Workflow status
        - current_phase: Current phase

        Args:
            filters: Dict of field names and values to filter by
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)

        Returns:
            List of WorkflowContext instances matching filters
        """
        if filters is None:
            filters = {}

        # Build WHERE clause
        where_clauses = []
        params = []

        for field, value in filters.items():
            if field in ['epic_num', 'story_num', 'feature', 'workflow_name', 'status', 'current_phase']:
                where_clauses.append(f"{field} = ?")
                params.append(value)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Build query with pagination
        query = f"SELECT context_data FROM workflow_context WHERE {where_sql} ORDER BY created_at DESC"
        if limit is not None:
            query += f" LIMIT {limit}"
        if offset is not None:
            query += f" OFFSET {offset}"

        with self._get_connection() as conn:
            cursor = conn.execute(query, params)

            contexts = []
            for row in cursor.fetchall():
                context_json = row['context_data']
                contexts.append(WorkflowContext.from_json(context_json))

            return contexts
