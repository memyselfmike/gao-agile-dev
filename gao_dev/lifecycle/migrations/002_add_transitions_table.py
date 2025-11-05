"""
Migration 002: Add Document Transitions Table.

This migration creates:
1. document_transitions table for audit trail of state changes
2. Indexes for efficient queries by document and date

Schema Version: 1.0.1
Created: 2024-11-05
"""

import sqlite3
from pathlib import Path


class Migration002:
    """Document transitions audit trail migration."""

    VERSION = "002"
    DESCRIPTION = "Add document_transitions table for audit trail"

    @staticmethod
    def up(conn: sqlite3.Connection) -> None:
        """
        Apply migration: create transitions table and indexes.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Create document_transitions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                from_state TEXT NOT NULL CHECK(from_state IN ('draft', 'active', 'obsolete', 'archived')),
                to_state TEXT NOT NULL CHECK(to_state IN ('draft', 'active', 'obsolete', 'archived')),
                reason TEXT NOT NULL,
                changed_by TEXT,
                changed_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
            """
        )

        # Create indexes for fast queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transitions_document "
            "ON document_transitions(document_id)"
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transitions_date "
            "ON document_transitions(changed_at)"
        )

        # Composite index for document-date queries (common pattern)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transitions_document_date "
            "ON document_transitions(document_id, changed_at DESC)"
        )

        # Record this migration
        cursor.execute(
            """
            INSERT OR IGNORE INTO schema_version (version, applied_at, description)
            VALUES (?, datetime('now'), ?)
            """,
            (Migration002.VERSION, Migration002.DESCRIPTION),
        )

        conn.commit()

    @staticmethod
    def down(conn: sqlite3.Connection) -> None:
        """
        Rollback migration: drop transitions table.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Drop transitions table
        cursor.execute("DROP TABLE IF EXISTS document_transitions")

        # Remove migration record
        cursor.execute(
            "DELETE FROM schema_version WHERE version = ?", (Migration002.VERSION,)
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
            (Migration002.VERSION,),
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
            if not Migration002.is_applied(conn):
                print(f"Applying migration {Migration002.VERSION}...")
                Migration002.up(conn)
                print(f"Migration {Migration002.VERSION} applied successfully.")
            else:
                print(f"Migration {Migration002.VERSION} already applied.")
        else:
            if Migration002.is_applied(conn):
                print(f"Rolling back migration {Migration002.VERSION}...")
                Migration002.down(conn)
                print(f"Migration {Migration002.VERSION} rolled back successfully.")
            else:
                print(f"Migration {Migration002.VERSION} not applied.")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python 002_add_transitions_table.py <db_path> [up|down]")
        sys.exit(1)

    db_path = Path(sys.argv[1])
    direction = sys.argv[2] if len(sys.argv) > 2 else "up"

    run_migration(db_path, direction)
