"""
Migration 003: Add Document Reviews Table.

This migration creates:
1. document_reviews table for tracking review history
2. Indexes for efficient queries by document and date
3. Foreign key to documents table with cascade delete

Schema Version: 1.0.2
Created: 2024-11-05
"""

import sqlite3
from pathlib import Path


class Migration003:
    """Document reviews tracking migration."""

    VERSION = "003"
    DESCRIPTION = "Add document_reviews table for governance tracking"

    @staticmethod
    def up(conn: sqlite3.Connection) -> None:
        """
        Apply migration: create reviews table and indexes.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Create document_reviews table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                reviewer TEXT NOT NULL,
                reviewed_at TEXT NOT NULL,
                notes TEXT,
                next_review_due TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
            """
        )

        # Create indexes for fast queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_document "
            "ON document_reviews(document_id)"
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_date "
            "ON document_reviews(reviewed_at)"
        )

        # Composite index for document-date queries (common pattern)
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_document_date "
            "ON document_reviews(document_id, reviewed_at DESC)"
        )

        # Index on reviewer for "get my review history" queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_reviewer "
            "ON document_reviews(reviewer)"
        )

        # Index on next_review_due for finding upcoming reviews
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_reviews_next_due "
            "ON document_reviews(next_review_due)"
        )

        # Record this migration
        cursor.execute(
            """
            INSERT OR IGNORE INTO schema_version (version, applied_at, description)
            VALUES (?, datetime('now'), ?)
            """,
            (Migration003.VERSION, Migration003.DESCRIPTION),
        )

        conn.commit()

    @staticmethod
    def down(conn: sqlite3.Connection) -> None:
        """
        Rollback migration: drop reviews table.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Drop reviews table
        cursor.execute("DROP TABLE IF EXISTS document_reviews")

        # Remove migration record
        cursor.execute(
            "DELETE FROM schema_version WHERE version = ?", (Migration003.VERSION,)
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
            (Migration003.VERSION,),
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
            if not Migration003.is_applied(conn):
                print(f"Applying migration {Migration003.VERSION}...")
                Migration003.up(conn)
                print(f"Migration {Migration003.VERSION} applied successfully.")
            else:
                print(f"Migration {Migration003.VERSION} already applied.")
        else:
            if Migration003.is_applied(conn):
                print(f"Rolling back migration {Migration003.VERSION}...")
                Migration003.down(conn)
                print(f"Migration {Migration003.VERSION} rolled back successfully.")
            else:
                print(f"Migration {Migration003.VERSION} not applied.")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python 003_add_reviews_table.py <db_path> [up|down]")
        sys.exit(1)

    db_path = Path(sys.argv[1])
    direction = sys.argv[2] if len(sys.argv) > 2 else "up"

    run_migration(db_path, direction)
