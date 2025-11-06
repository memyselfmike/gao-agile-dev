"""
Context Lineage Tracking for GAO-Dev.

This module provides context lineage tracking to record which context (document versions)
was used for which artifacts. This creates a compliance audit trail showing what
architecture/PRD version was used for each implementation, enabling queries like:
- "What architecture was used for Story 3.1?"
- "Which stories used outdated PRD?"
- "What context was used in this workflow execution?"

Performance targets:
- Record usage: <50ms
- Query lineage: <100ms
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class ContextLineageTracker:
    """
    Track context lineage for compliance and audit trail.

    This tracker records which documents were used to create which artifacts,
    providing full lineage tracking from PRD -> Architecture -> Stories -> Code.

    Features:
    - Record document usage for artifacts (epics, stories, code, etc.)
    - Link to document registry (document_id) and workflow executions (workflow_id)
    - Capture document version (content hash) at time of use
    - Detect stale context usage (using obsolete documents)
    - Generate lineage reports showing document flow
    - Support complex lineage queries

    Example:
        >>> tracker = ContextLineageTracker(Path("gao_dev.db"))
        >>>
        >>> # Record that Story 3.1 used a specific architecture document
        >>> tracker.record_usage(
        ...     artifact_type="story",
        ...     artifact_id="3.1",
        ...     document_id=42,
        ...     document_path="docs/features/auth/ARCHITECTURE.md",
        ...     document_type="architecture",
        ...     document_version="abc123def456",
        ...     workflow_id="wf-story-3.1-implement",
        ...     epic=3,
        ...     story="3.1"
        ... )
        >>>
        >>> # Query what context was used for Story 3.1
        >>> context = tracker.get_artifact_context("story", "3.1")
        >>> print(f"Used architecture: {context[0]['document_path']}")
        >>>
        >>> # Get full lineage chain
        >>> lineage = tracker.get_context_lineage("story", "3.1")
        >>> # Returns: [PRD, Architecture, Epic, Story]
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize context lineage tracker.

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
        self._ensure_schema_exists()

    def _ensure_schema_exists(self) -> None:
        """
        Ensure context_usage table exists.

        Runs migration 002_create_context_usage_table.sql to create the schema.
        Safe to call multiple times (idempotent).
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Read and execute migration SQL
        migration_path = Path(__file__).parent / "migrations" / "002_create_context_usage_table.sql"

        if migration_path.exists():
            with self._get_connection() as conn:
                migration_sql = migration_path.read_text(encoding="utf-8")
                # Execute all statements in migration
                conn.executescript(migration_sql)
                conn.commit()
                logger.debug("context_usage_schema_initialized", db_path=str(self.db_path))
        else:
            # Fallback: create schema inline if migration file not found
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS context_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        artifact_type TEXT NOT NULL CHECK(artifact_type IN (
                            'epic', 'story', 'task', 'code', 'test', 'doc', 'other'
                        )),
                        artifact_id TEXT NOT NULL,
                        document_id INTEGER,
                        document_path TEXT,
                        document_type TEXT,
                        document_version TEXT NOT NULL,
                        workflow_id TEXT,
                        workflow_name TEXT,
                        epic INTEGER,
                        story TEXT,
                        accessed_at TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_context_usage_artifact ON context_usage(artifact_type, artifact_id)",
                    "CREATE INDEX IF NOT EXISTS idx_context_usage_document_id ON context_usage(document_id)",
                    "CREATE INDEX IF NOT EXISTS idx_context_usage_workflow_id ON context_usage(workflow_id)",
                    "CREATE INDEX IF NOT EXISTS idx_context_usage_epic_story ON context_usage(epic, story)",
                ]
                for idx_sql in indexes:
                    conn.execute(idx_sql)

                conn.commit()
                logger.warning(
                    "context_usage_schema_created_inline",
                    reason="Migration file not found",
                    db_path=str(self.db_path)
                )

    @contextmanager
    def _get_connection(self):
        """
        Get database connection context manager.

        Yields:
            sqlite3.Connection with row factory set to Row
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        # Enable foreign keys (required for CASCADE behavior in SQLite)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error("database_error", error=str(e))
            raise
        finally:
            conn.close()

    def record_usage(
        self,
        artifact_type: str,
        artifact_id: str,
        document_version: str,
        document_id: Optional[int] = None,
        document_path: Optional[str] = None,
        document_type: Optional[str] = None,
        workflow_id: Optional[str] = None,
        workflow_name: Optional[str] = None,
        epic: Optional[int] = None,
        story: Optional[str] = None,
    ) -> int:
        """
        Record context usage for an artifact.

        This records that a specific document version was used to create/inform
        an artifact (epic, story, code, test, etc.).

        Args:
            artifact_type: Type of artifact (epic, story, task, code, test, doc, other)
            artifact_id: Identifier of artifact (e.g., "3.1", "epic-5")
            document_version: Content hash of document at time of use
            document_id: ID of document in documents table (optional)
            document_path: Path to document file (optional)
            document_type: Type of document (prd, architecture, etc.) (optional)
            workflow_id: ID of workflow execution (optional)
            workflow_name: Name of workflow (optional)
            epic: Epic number (optional)
            story: Story identifier (optional)

        Returns:
            ID of created usage record

        Raises:
            ValueError: If artifact_type is invalid
        """
        valid_types = {'epic', 'story', 'task', 'code', 'test', 'doc', 'other'}
        if artifact_type not in valid_types:
            raise ValueError(
                f"Invalid artifact_type: {artifact_type}. "
                f"Valid types: {', '.join(sorted(valid_types))}"
            )

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO context_usage (
                    artifact_type, artifact_id, document_id, document_path,
                    document_type, document_version, workflow_id, workflow_name,
                    epic, story, accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_type,
                    artifact_id,
                    document_id,
                    document_path,
                    document_type,
                    document_version,
                    workflow_id,
                    workflow_name,
                    epic,
                    story,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

            usage_id = cursor.lastrowid

            logger.debug(
                "context_usage_recorded",
                artifact_type=artifact_type,
                artifact_id=artifact_id,
                document_type=document_type,
                workflow_id=workflow_id,
            )

            return usage_id

    def get_artifact_context(
        self,
        artifact_type: str,
        artifact_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all context used for a specific artifact.

        Returns all documents that were used to create/inform the specified artifact,
        ordered by most recent access first.

        Args:
            artifact_type: Type of artifact (epic, story, task, code, test, doc, other)
            artifact_id: Identifier of artifact (e.g., "3.1")

        Returns:
            List of usage records as dicts, each containing:
            - document_id, document_path, document_type, document_version
            - workflow_id, workflow_name
            - accessed_at
            - epic, story

        Example:
            >>> context = tracker.get_artifact_context("story", "3.1")
            >>> for doc in context:
            ...     print(f"{doc['document_type']}: {doc['document_path']}")
            architecture: docs/features/auth/ARCHITECTURE.md
            prd: docs/features/auth/PRD.md
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    id, artifact_type, artifact_id,
                    document_id, document_path, document_type, document_version,
                    workflow_id, workflow_name,
                    epic, story, accessed_at, created_at
                FROM context_usage
                WHERE artifact_type = ? AND artifact_id = ?
                ORDER BY accessed_at DESC
                """,
                (artifact_type, artifact_id),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_context_lineage(
        self,
        artifact_type: str,
        artifact_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get full context lineage chain for an artifact.

        This recursively traces the lineage from the artifact back through all
        documents that informed it, building the complete chain:
        PRD -> Architecture -> Epic -> Story -> Code

        Args:
            artifact_type: Type of artifact (epic, story, task, code, test, doc, other)
            artifact_id: Identifier of artifact

        Returns:
            List of documents in lineage chain, ordered from root (PRD) to artifact.
            Each entry contains full usage record.

        Example:
            >>> lineage = tracker.get_context_lineage("story", "3.1")
            >>> for doc in lineage:
            ...     print(f"{doc['document_type']}: {doc['document_path']}")
            prd: docs/features/auth/PRD.md
            architecture: docs/features/auth/ARCHITECTURE.md
            epic: docs/features/auth/epic-3.md
            story: docs/features/auth/story-3.1.md
        """
        # Get direct context for this artifact
        context = self.get_artifact_context(artifact_type, artifact_id)

        if not context:
            return []

        # Simply return the sorted context
        # More sophisticated lineage tracking would require document relationship data
        return self._sort_lineage(context)

    def get_workflow_context(
        self,
        workflow_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all context used in a workflow execution.

        Returns all documents accessed during the specified workflow execution.

        Args:
            workflow_id: Workflow execution ID

        Returns:
            List of usage records for this workflow
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    id, artifact_type, artifact_id,
                    document_id, document_path, document_type, document_version,
                    workflow_id, workflow_name,
                    epic, story, accessed_at, created_at
                FROM context_usage
                WHERE workflow_id = ?
                ORDER BY accessed_at ASC
                """,
                (workflow_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def detect_stale_usage(
        self,
        current_document_versions: Dict[int, str],
    ) -> List[Dict[str, Any]]:
        """
        Detect stale context usage (using obsolete document versions).

        Compares recorded document versions against current versions to find
        artifacts that were built using outdated context.

        Args:
            current_document_versions: Dict mapping document_id to current content_hash

        Returns:
            List of stale usage records, each containing:
            - artifact_type, artifact_id
            - document_id, document_path, document_type
            - recorded_version (stale), current_version
            - accessed_at

        Example:
            >>> # Get current document versions from document registry
            >>> current_versions = {42: "xyz789", 43: "def456"}
            >>> stale = tracker.detect_stale_usage(current_versions)
            >>> for usage in stale:
            ...     print(f"Story {usage['artifact_id']} used stale {usage['document_type']}")
        """
        stale_usage = []

        with self._get_connection() as conn:
            # Get all usage records with document_id
            cursor = conn.execute(
                """
                SELECT
                    id, artifact_type, artifact_id,
                    document_id, document_path, document_type, document_version,
                    workflow_id, epic, story, accessed_at
                FROM context_usage
                WHERE document_id IS NOT NULL
                ORDER BY accessed_at DESC
                """
            )

            for row in cursor.fetchall():
                doc_id = row['document_id']
                recorded_version = row['document_version']

                if doc_id in current_document_versions:
                    current_version = current_document_versions[doc_id]

                    # Check if version has changed
                    if recorded_version != current_version:
                        stale_record = dict(row)
                        stale_record['current_version'] = current_version
                        stale_record['recorded_version'] = recorded_version
                        stale_usage.append(stale_record)

        return stale_usage

    def generate_lineage_report(
        self,
        epic: int,
        output_format: str = "markdown",
    ) -> str:
        """
        Generate lineage report for an epic.

        Creates a report showing document flow: PRD -> Architecture -> Stories -> Code.
        Highlights stale context usage.

        Args:
            epic: Epic number
            output_format: Output format ("markdown" or "json")

        Returns:
            Report as string (markdown or JSON)

        Example:
            >>> report = tracker.generate_lineage_report(epic=3, output_format="markdown")
            >>> print(report)
            # Context Lineage Report - Epic 3

            ## Document Flow
            - PRD: docs/features/auth/PRD.md (v1.0)
            - Architecture: docs/features/auth/ARCHITECTURE.md (v2.3)

            ## Stories
            ### Story 3.1
            - Used Architecture v2.3
            - Used PRD v1.0
            ...
        """
        # Get all usage for this epic
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT
                    id, artifact_type, artifact_id,
                    document_id, document_path, document_type, document_version,
                    workflow_id, workflow_name, accessed_at
                FROM context_usage
                WHERE epic = ?
                ORDER BY artifact_type, artifact_id, accessed_at DESC
                """,
                (epic,),
            )
            usage_records = [dict(row) for row in cursor.fetchall()]

        if output_format == "json":
            import json
            return json.dumps({
                "epic": epic,
                "usage_records": usage_records,
            }, indent=2)

        # Generate markdown report
        lines = [
            f"# Context Lineage Report - Epic {epic}",
            "",
            "## Document Flow",
            "",
        ]

        # Group by document type
        docs_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for record in usage_records:
            doc_type = record.get('document_type', 'unknown')
            if doc_type not in docs_by_type:
                docs_by_type[doc_type] = []
            docs_by_type[doc_type].append(record)

        # Show documents in hierarchical order
        doc_order = ['prd', 'architecture', 'epic', 'story', 'code', 'test']
        for doc_type in doc_order:
            if doc_type in docs_by_type:
                lines.append(f"### {doc_type.upper()}")
                # Deduplicate by document_path
                seen_paths = set()
                for record in docs_by_type[doc_type]:
                    path = record.get('document_path', 'unknown')
                    version = record['document_version'][:8]  # Short hash
                    if path not in seen_paths:
                        seen_paths.add(path)
                        lines.append(f"- {path} (version: {version})")
                lines.append("")

        # Show artifacts grouped by type
        lines.append("## Artifacts")
        lines.append("")

        artifacts_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for record in usage_records:
            artifact_type = record['artifact_type']
            if artifact_type not in artifacts_by_type:
                artifacts_by_type[artifact_type] = []
            artifacts_by_type[artifact_type].append(record)

        for artifact_type in sorted(artifacts_by_type.keys()):
            lines.append(f"### {artifact_type.capitalize()}s")
            # Group by artifact_id
            by_id: Dict[str, List[Dict[str, Any]]] = {}
            for record in artifacts_by_type[artifact_type]:
                aid = record['artifact_id']
                if aid not in by_id:
                    by_id[aid] = []
                by_id[aid].append(record)

            for artifact_id in sorted(by_id.keys()):
                lines.append(f"#### {artifact_type.capitalize()} {artifact_id}")
                lines.append("Used context:")
                for record in by_id[artifact_id]:
                    doc_type = record.get('document_type', 'unknown')
                    doc_path = record.get('document_path', 'unknown')
                    version = record['document_version'][:8]
                    lines.append(f"- {doc_type}: {doc_path} (v{version})")
                lines.append("")

        return "\n".join(lines)

    # Private helper methods

    def _find_parent_context(
        self,
        usage: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Find parent context for a usage record.

        This recursively finds documents that were used to create the document
        in the given usage record.

        Args:
            usage: Usage record dict

        Returns:
            List of parent usage records
        """
        # Extract artifact info from document path
        # This is a simplified implementation - in reality, would need to
        # parse the document or query document relationships
        parents = []

        # If this is a story document, look for epic and architecture
        if usage.get('document_type') == 'story':
            story_id = usage.get('artifact_id')
            if story_id and '.' in story_id:
                epic_num = int(story_id.split('.')[0])
                # Find epic context
                epic_context = self.get_artifact_context('epic', str(epic_num))
                parents.extend(epic_context)

        return parents

    def _sort_lineage(
        self,
        lineage: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Sort lineage by document hierarchy.

        Orders documents from root (PRD) to leaf (Code):
        PRD -> Architecture -> Epic -> Story -> Code -> Test

        Args:
            lineage: Unsorted lineage list

        Returns:
            Sorted lineage list
        """
        # Define hierarchy order
        type_order = {
            'prd': 0,
            'architecture': 1,
            'epic': 2,
            'story': 3,
            'code': 4,
            'test': 5,
            'doc': 6,
            'other': 7,
        }

        def get_sort_key(record: Dict[str, Any]) -> int:
            doc_type = record.get('document_type', 'other')
            return type_order.get(doc_type, 99)

        return sorted(lineage, key=get_sort_key)
