"""
Migration 005: Add State Tracking Tables.

This migration creates:
1. epic_state table for fast epic progress queries
2. story_state table for fast story status queries
3. action_items table for active action item tracking
4. ceremony_summaries table for ceremony outcomes index
5. learning_index table for topical learning index
6. All necessary indexes for <5ms query performance

Schema Version: 1.0.4
Created: 2025-11-09
Epic: 24 - State Tables & Tracker
Story: 24.1 - Create Migration 005 (State Tables)
"""

import sqlite3
from pathlib import Path


class Migration005:
    """State tracking tables migration."""

    VERSION = "005"
    DESCRIPTION = "Add state tracking tables for epic, story, actions, ceremonies, and learning"

    @staticmethod
    def up(conn: sqlite3.Connection) -> None:
        """
        Apply migration: create all state tracking tables and indexes.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")

        # Create epic_state table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS epic_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epic_num INTEGER UNIQUE NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN (
                    'planning', 'in_progress', 'blocked', 'completed', 'archived'
                )),
                total_stories INTEGER NOT NULL DEFAULT 0,
                completed_stories INTEGER NOT NULL DEFAULT 0,
                progress_percentage REAL NOT NULL DEFAULT 0.0,
                started_at TEXT,
                completed_at TEXT,
                blocked_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata JSON
            )
            """
        )

        # Create story_state table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS story_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                epic_num INTEGER NOT NULL,
                story_num INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN (
                    'pending', 'in_progress', 'review', 'testing', 'completed', 'blocked'
                )),
                assignee TEXT,
                priority TEXT CHECK(priority IN ('P0', 'P1', 'P2', 'P3')) DEFAULT 'P2',
                estimate_hours REAL,
                actual_hours REAL,
                started_at TEXT,
                completed_at TEXT,
                blocked_reason TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata JSON,
                UNIQUE(epic_num, story_num),
                FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE CASCADE
            )
            """
        )

        # Create action_items table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS action_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL CHECK(status IN (
                    'pending', 'in_progress', 'completed', 'cancelled'
                )) DEFAULT 'pending',
                priority TEXT CHECK(priority IN ('high', 'medium', 'low')) DEFAULT 'medium',
                assignee TEXT,
                epic_num INTEGER,
                story_num INTEGER,
                due_date TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                updated_at TEXT NOT NULL,
                metadata JSON,
                FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE SET NULL
            )
            """
        )

        # Create ceremony_summaries table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ceremony_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ceremony_type TEXT NOT NULL CHECK(ceremony_type IN (
                    'planning', 'standup', 'review', 'retrospective', 'refinement'
                )),
                epic_num INTEGER,
                story_num INTEGER,
                summary TEXT NOT NULL,
                participants TEXT,
                decisions TEXT,
                action_items TEXT,
                held_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata JSON,
                FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE SET NULL
            )
            """
        )

        # Create learning_index table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                category TEXT NOT NULL CHECK(category IN (
                    'technical', 'process', 'domain', 'architectural', 'team'
                )),
                learning TEXT NOT NULL,
                context TEXT,
                source_type TEXT CHECK(source_type IN (
                    'retrospective', 'postmortem', 'code_review', 'incident', 'experiment'
                )),
                epic_num INTEGER,
                story_num INTEGER,
                relevance_score REAL DEFAULT 1.0,
                superseded_by INTEGER,
                is_active INTEGER NOT NULL DEFAULT 1,
                indexed_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata JSON,
                FOREIGN KEY (epic_num) REFERENCES epic_state(epic_num) ON DELETE SET NULL,
                FOREIGN KEY (superseded_by) REFERENCES learning_index(id) ON DELETE SET NULL
            )
            """
        )

        # Create indexes for epic_state
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_epic_state_status ON epic_state(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_epic_state_progress ON epic_state(progress_percentage)"
        )

        # Create indexes for story_state
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_story_state_epic ON story_state(epic_num)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_story_state_status ON story_state(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_story_state_assignee ON story_state(assignee)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_story_state_priority ON story_state(priority)"
        )
        # Composite index for common query pattern: epic + status
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_story_state_epic_status "
            "ON story_state(epic_num, status)"
        )

        # Create indexes for action_items
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_action_items_assignee ON action_items(assignee)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_action_items_due_date ON action_items(due_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_action_items_epic ON action_items(epic_num)"
        )
        # Composite index for active items query
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_action_items_status_due "
            "ON action_items(status, due_date)"
        )

        # Create indexes for ceremony_summaries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ceremony_type ON ceremony_summaries(ceremony_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ceremony_epic ON ceremony_summaries(epic_num)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ceremony_held_at ON ceremony_summaries(held_at DESC)"
        )
        # Composite index for type + date queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ceremony_type_date "
            "ON ceremony_summaries(ceremony_type, held_at DESC)"
        )

        # Create indexes for learning_index
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_learning_topic ON learning_index(topic)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_learning_category ON learning_index(category)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_learning_active ON learning_index(is_active)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_learning_relevance ON learning_index(relevance_score DESC)"
        )
        # Composite index for search queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_learning_active_category "
            "ON learning_index(is_active, category, relevance_score DESC)"
        )

        # Record this migration
        cursor.execute(
            """
            INSERT OR IGNORE INTO schema_version (version, applied_at, description)
            VALUES (?, datetime('now'), ?)
            """,
            (Migration005.VERSION, Migration005.DESCRIPTION),
        )

        conn.commit()

    @staticmethod
    def down(conn: sqlite3.Connection) -> None:
        """
        Rollback migration: drop all state tracking tables.

        Args:
            conn: SQLite database connection
        """
        cursor = conn.cursor()

        # Drop tables in reverse dependency order
        cursor.execute("DROP TABLE IF EXISTS learning_index")
        cursor.execute("DROP TABLE IF EXISTS ceremony_summaries")
        cursor.execute("DROP TABLE IF EXISTS action_items")
        cursor.execute("DROP TABLE IF EXISTS story_state")
        cursor.execute("DROP TABLE IF EXISTS epic_state")

        # Remove migration record
        cursor.execute(
            "DELETE FROM schema_version WHERE version = ?", (Migration005.VERSION,)
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
            (Migration005.VERSION,),
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
            if not Migration005.is_applied(conn):
                print(f"Applying migration {Migration005.VERSION}...")
                Migration005.up(conn)
                print(f"Migration {Migration005.VERSION} applied successfully.")
            else:
                print(f"Migration {Migration005.VERSION} already applied.")
        else:
            if Migration005.is_applied(conn):
                print(f"Rolling back migration {Migration005.VERSION}...")
                Migration005.down(conn)
                print(f"Migration {Migration005.VERSION} rolled back successfully.")
            else:
                print(f"Migration {Migration005.VERSION} not applied.")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python 005_add_state_tables.py <db_path> [up|down]")
        sys.exit(1)

    db_path = Path(sys.argv[1])
    direction = sys.argv[2] if len(sys.argv) > 2 else "up"

    run_migration(db_path, direction)
