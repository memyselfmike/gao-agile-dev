"""
Migration 001: Create Initial Document Registry Schema.

This migration creates:
1. documents table with all core and governance fields
2. document_relationships table for linking documents
3. All necessary indexes for performance
4. FTS5 virtual table schema (prepared for Story 12.9)

Schema Version: 1.0.0
Created: 2024-11-05
"""

import sqlite3
from pathlib import Path


class Migration001:
    """Initial schema creation migration."""

    VERSION = "001"
    DESCRIPTION = "Create initial document registry schema"

    @staticmethod
    def up(conn: sqlite3.Connection) -> None:
        """
        Apply migration: create all tables and indexes.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Create documents table with governance fields
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL CHECK(type IN (
                    'prd', 'architecture', 'epic', 'story', 'adr',
                    'postmortem', 'runbook', 'qa_report', 'test_report'
                )),
                state TEXT NOT NULL CHECK(state IN (
                    'draft', 'active', 'obsolete', 'archived'
                )),
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL,
                author TEXT,
                feature TEXT,
                epic INTEGER,
                story TEXT,
                content_hash TEXT,

                -- Governance fields (ENHANCED in Epic 12)
                owner TEXT,
                reviewer TEXT,
                review_due_date TEXT,

                -- Extensible metadata stored as JSON
                metadata JSON
            )
            """
        )

        # Create document_relationships table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_relationships (
                parent_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                child_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                relationship_type TEXT NOT NULL CHECK(relationship_type IN (
                    'derived_from', 'implements', 'tests', 'replaces', 'references'
                )),
                PRIMARY KEY (parent_id, child_id, relationship_type)
            )
            """
        )

        # Create indexes for fast queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_state ON documents(state)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_feature ON documents(feature)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_epic ON documents(epic)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner)"
        )

        # Composite indexes for common query patterns
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_type_state "
            "ON documents(type, state)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_feature_type "
            "ON documents(feature, type)"
        )

        # Index on modified_at for sorting by recency
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_modified_at "
            "ON documents(modified_at)"
        )

        # Index on review_due_date for governance queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_documents_review_due_date "
            "ON documents(review_due_date)"
        )

        # Index on relationship type for fast relationship queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_relationships_type "
            "ON document_relationships(relationship_type)"
        )

        # Create schema_version table to track migrations
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL,
                description TEXT
            )
            """
        )

        # Record this migration
        cursor.execute(
            """
            INSERT OR IGNORE INTO schema_version (version, applied_at, description)
            VALUES (?, datetime('now'), ?)
            """,
            (Migration001.VERSION, Migration001.DESCRIPTION),
        )

        # Prepare FTS5 virtual table for full-text search (Story 12.9)
        # NOTE: Triggers will be activated in Story 12.9
        cursor.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                path,
                content,
                content=documents,
                content_rowid=id,
                tokenize='porter unicode61'
            )
            """
        )

        conn.commit()

    @staticmethod
    def down(conn: sqlite3.Connection) -> None:
        """
        Rollback migration: drop all tables.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Drop FTS5 table
        cursor.execute("DROP TABLE IF EXISTS documents_fts")

        # Drop main tables
        cursor.execute("DROP TABLE IF EXISTS document_relationships")
        cursor.execute("DROP TABLE IF EXISTS documents")

        # Remove migration record
        cursor.execute(
            "DELETE FROM schema_version WHERE version = ?", (Migration001.VERSION,)
        )

        conn.commit()

    @staticmethod
    def is_applied(conn: sqlite3.Connection) -> bool:
        """
        Check if this migration has been applied.

        Args:
            conn: SQLite database connection

        Returns:
            True if migration is applied, False otherwise
        """
        cursor = conn.cursor()

        # Check if schema_version table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='schema_version'
            """
        )

        if not cursor.fetchone():
            return False

        # Check if this version is recorded
        cursor.execute(
            "SELECT version FROM schema_version WHERE version = ?",
            (Migration001.VERSION,),
        )

        return cursor.fetchone() is not None


def run_migration(db_path: Path, direction: str = "up") -> None:
    """
    Run migration on specified database.

    Args:
        db_path: Path to SQLite database file
        direction: 'up' to apply, 'down' to rollback

    Raises:
        ValueError: If direction is invalid
    """
    if direction not in ["up", "down"]:
        raise ValueError(f"Invalid direction: {direction}. Must be 'up' or 'down'.")

    conn = sqlite3.connect(str(db_path))

    try:
        if direction == "up":
            if not Migration001.is_applied(conn):
                print(f"Applying migration {Migration001.VERSION}...")
                Migration001.up(conn)
                print(f"Migration {Migration001.VERSION} applied successfully.")
            else:
                print(f"Migration {Migration001.VERSION} already applied.")
        else:
            if Migration001.is_applied(conn):
                print(f"Rolling back migration {Migration001.VERSION}...")
                Migration001.down(conn)
                print(f"Migration {Migration001.VERSION} rolled back successfully.")
            else:
                print(f"Migration {Migration001.VERSION} not applied.")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python 001_create_schema.py <db_path> [up|down]")
        sys.exit(1)

    db_path = Path(sys.argv[1])
    direction = sys.argv[2] if len(sys.argv) > 2 else "up"

    run_migration(db_path, direction)
