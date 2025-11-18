"""Migration 002: Add message threading support.

Story 39.34: Message Threading Infrastructure

Creates threads and messages tables for single-level message threading.
"""

import sqlite3
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger()


class Migration002:
    """Add message threading support to database."""

    version = 2
    description = "Add threads and messages tables for message threading"

    @staticmethod
    def upgrade(db_path: Path) -> bool:
        """Apply migration to add threading support.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful

        Raises:
            Exception: If migration fails
        """
        try:
            with sqlite3.connect(str(db_path)) as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Check if migration already applied
                cursor = conn.execute(
                    "SELECT version FROM schema_version WHERE version = ?",
                    (Migration002.version,),
                )
                if cursor.fetchone():
                    logger.info(
                        "migration_already_applied",
                        version=Migration002.version,
                    )
                    return True

                # Create threads table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS threads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        parent_message_id TEXT NOT NULL UNIQUE,
                        conversation_id TEXT NOT NULL,
                        conversation_type TEXT NOT NULL CHECK(conversation_type IN ('dm', 'channel')),
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),

                        -- Denormalized count for performance
                        reply_count INTEGER NOT NULL DEFAULT 0,

                        -- Metadata
                        metadata JSON
                    )
                """)

                # Create messages table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        conversation_type TEXT NOT NULL CHECK(conversation_type IN ('dm', 'channel')),

                        -- Message content
                        content TEXT NOT NULL,
                        role TEXT NOT NULL CHECK(role IN ('user', 'agent')),

                        -- Agent info (for agent messages)
                        agent_id TEXT,
                        agent_name TEXT,

                        -- Threading
                        thread_id INTEGER REFERENCES threads(id) ON DELETE CASCADE,
                        reply_to_message_id TEXT,
                        thread_count INTEGER NOT NULL DEFAULT 0,

                        -- Timestamps
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),

                        -- Metadata
                        metadata JSON
                    )
                """)

                # Create indexes for performance
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_threads_parent_message ON threads(parent_message_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_threads_conversation ON threads(conversation_id, conversation_type)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, conversation_type)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at)"
                )

                # Create trigger for updating threads.updated_at
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_thread_timestamp
                    AFTER UPDATE ON threads
                    FOR EACH ROW
                    BEGIN
                        UPDATE threads SET updated_at = datetime('now') WHERE id = NEW.id;
                    END
                """)

                # Create trigger for updating messages.updated_at
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_message_timestamp
                    AFTER UPDATE ON messages
                    FOR EACH ROW
                    BEGIN
                        UPDATE messages SET updated_at = datetime('now') WHERE id = NEW.id;
                    END
                """)

                # Create trigger to increment thread reply_count when message added
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS increment_thread_reply_count
                    AFTER INSERT ON messages
                    FOR EACH ROW
                    WHEN NEW.thread_id IS NOT NULL
                    BEGIN
                        UPDATE threads
                        SET reply_count = reply_count + 1
                        WHERE id = NEW.thread_id;
                    END
                """)

                # Create trigger to update parent message thread_count
                # This runs AFTER the increment_thread_reply_count trigger
                conn.execute("""
                    CREATE TRIGGER IF NOT EXISTS update_parent_thread_count
                    AFTER UPDATE ON threads
                    FOR EACH ROW
                    WHEN NEW.reply_count != OLD.reply_count
                    BEGIN
                        UPDATE messages
                        SET thread_count = NEW.reply_count
                        WHERE id = NEW.parent_message_id;
                    END
                """)

                # Record migration
                conn.execute(
                    """
                    INSERT INTO schema_version (version, description)
                    VALUES (?, ?)
                """,
                    (Migration002.version, Migration002.description),
                )

                conn.commit()

                logger.info(
                    "migration_applied",
                    version=Migration002.version,
                    description=Migration002.description,
                )

                return True

        except Exception as e:
            logger.error(
                "migration_failed", version=Migration002.version, error=str(e)
            )
            raise

    @staticmethod
    def downgrade(db_path: Path) -> bool:
        """Rollback migration.

        Args:
            db_path: Path to SQLite database

        Returns:
            True if successful

        Raises:
            Exception: If rollback fails
        """
        try:
            with sqlite3.connect(str(db_path)) as conn:
                # Drop triggers
                conn.execute("DROP TRIGGER IF EXISTS update_parent_thread_count")
                conn.execute("DROP TRIGGER IF EXISTS increment_thread_reply_count")
                conn.execute("DROP TRIGGER IF EXISTS update_message_timestamp")
                conn.execute("DROP TRIGGER IF EXISTS update_thread_timestamp")

                # Drop tables
                conn.execute("DROP TABLE IF EXISTS messages")
                conn.execute("DROP TABLE IF EXISTS threads")

                # Remove from version table
                conn.execute(
                    "DELETE FROM schema_version WHERE version = ?",
                    (Migration002.version,),
                )

                conn.commit()

                logger.info("migration_rolled_back", version=Migration002.version)
                return True

        except Exception as e:
            logger.error(
                "rollback_failed", version=Migration002.version, error=str(e)
            )
            raise
