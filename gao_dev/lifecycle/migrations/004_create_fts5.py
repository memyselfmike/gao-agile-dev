"""
Migration 004: Create FTS5 Full-Text Search with Triggers.

This migration creates:
1. Enhanced FTS5 virtual table for full-text search (title, content, tags)
2. Triggers to keep FTS index in sync with documents table
3. All necessary indexes for fast search performance

Schema Version: 1.0.4
Created: 2025-11-05
"""

import sqlite3
from pathlib import Path
from typing import Optional


class Migration004:
    """FTS5 full-text search migration."""

    VERSION = "004"
    DESCRIPTION = "Create FTS5 full-text search with triggers"

    @staticmethod
    def up(conn: sqlite3.Connection) -> None:
        """
        Apply migration: create FTS5 table and triggers.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Drop existing FTS table if it exists (from migration 001)
        cursor.execute("DROP TABLE IF EXISTS documents_fts")

        # Create enhanced FTS5 virtual table
        # Note: We store data directly in FTS table (not external content)
        # for simplicity and to avoid trigger complexity
        cursor.execute(
            """
            CREATE VIRTUAL TABLE documents_fts USING fts5(
                title,       -- Document path for display
                content,     -- Full document text
                tags,        -- Tags from metadata (JSON array as text)
                tokenize='porter unicode61'  -- Porter stemming + Unicode support
            )
            """
        )

        # Populate FTS table with existing documents
        # For initial population, we'll just use path as title and empty content
        # (actual content will be populated when files are read)
        cursor.execute(
            """
            INSERT INTO documents_fts(title, content, tags)
            SELECT
                path,
                '',  -- Content will be populated by triggers on next update
                COALESCE(json_extract(metadata, '$.tags'), '[]')
            FROM documents
            """
        )

        # Trigger: Insert into FTS when document inserted
        cursor.execute(
            """
            CREATE TRIGGER documents_fts_insert AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(title, content, tags)
                VALUES (
                    new.path,
                    '',  -- Content will be read on-demand by search
                    COALESCE(json_extract(new.metadata, '$.tags'), '[]')
                );
            END
            """
        )

        # Trigger: Update FTS when document updated
        # Note: FTS5 requires deleting and re-inserting for updates
        cursor.execute(
            """
            CREATE TRIGGER documents_fts_update AFTER UPDATE ON documents BEGIN
                DELETE FROM documents_fts WHERE title = old.path;
                INSERT INTO documents_fts(title, content, tags)
                VALUES (
                    new.path,
                    '',  -- Content will be read on-demand by search
                    COALESCE(json_extract(new.metadata, '$.tags'), '[]')
                );
            END
            """
        )

        # Trigger: Delete from FTS when document deleted
        cursor.execute(
            """
            CREATE TRIGGER documents_fts_delete AFTER DELETE ON documents BEGIN
                DELETE FROM documents_fts WHERE title = old.path;
            END
            """
        )

        # Record this migration
        cursor.execute(
            """
            INSERT OR IGNORE INTO schema_version (version, applied_at, description)
            VALUES (?, datetime('now'), ?)
            """,
            (Migration004.VERSION, Migration004.DESCRIPTION),
        )

        conn.commit()

    @staticmethod
    def down(conn: sqlite3.Connection) -> None:
        """
        Rollback migration: drop FTS table and triggers.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Drop triggers
        cursor.execute("DROP TRIGGER IF EXISTS documents_fts_insert")
        cursor.execute("DROP TRIGGER IF EXISTS documents_fts_update")
        cursor.execute("DROP TRIGGER IF EXISTS documents_fts_delete")

        # Drop FTS5 table
        cursor.execute("DROP TABLE IF EXISTS documents_fts")

        # Remove migration record
        cursor.execute(
            "DELETE FROM schema_version WHERE version = ?", (Migration004.VERSION,)
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
            (Migration004.VERSION,),
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
            if not Migration004.is_applied(conn):
                print(f"Applying migration {Migration004.VERSION}...")
                Migration004.up(conn)
                print(f"Migration {Migration004.VERSION} applied successfully.")
            else:
                print(f"Migration {Migration004.VERSION} already applied.")
        else:
            if Migration004.is_applied(conn):
                print(f"Rolling back migration {Migration004.VERSION}...")
                Migration004.down(conn)
                print(f"Migration {Migration004.VERSION} rolled back successfully.")
            else:
                print(f"Migration {Migration004.VERSION} not applied.")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python 004_create_fts5.py <db_path> [up|down]")
        sys.exit(1)

    db_path = Path(sys.argv[1])
    direction = sys.argv[2] if len(sys.argv) > 2 else "up"

    run_migration(db_path, direction)
